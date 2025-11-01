Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Supabase configuration missing');
        }

        // Check for unresolved circuit breaker events
        const circuitBreakerResponse = await fetch(
            `${supabaseUrl}/rest/v1/circuit_breaker_events?resolved=eq.false`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const circuitBreakers = await circuitBreakerResponse.json();

        // Check for critical risk alerts
        const alertsResponse = await fetch(
            `${supabaseUrl}/rest/v1/risk_alerts?resolved=eq.false&severity=eq.critical`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const criticalAlerts = await alertsResponse.json();

        // Calculate recent loss rate
        const oneHourAgo = new Date();
        oneHourAgo.setHours(oneHourAgo.getHours() - 1);

        const recentTradesResponse = await fetch(
            `${supabaseUrl}/rest/v1/trades?created_at=gte.${oneHourAgo.toISOString()}`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const recentTrades = await recentTradesResponse.json();
        
        const recentLosses = recentTrades.filter(t => {
            const profit = parseFloat(t.actual_profit || t.expected_profit || 0);
            return profit < 0;
        });

        const totalLoss = recentLosses.reduce((sum, t) => {
            const profit = parseFloat(t.actual_profit || t.expected_profit || 0);
            return sum + Math.abs(profit);
        }, 0);

        const lossRate = recentTrades.length > 0 ? 
            recentLosses.length / recentTrades.length : 0;

        const consecutiveLosses = calculateConsecutiveLosses(recentTrades);

        // Check thresholds and trigger alerts
        const issues = [];
        
        if (circuitBreakers.length > 0) {
            issues.push({
                type: 'circuit_breaker_active',
                severity: 'critical',
                count: circuitBreakers.length,
                message: `${circuitBreakers.length} circuit breaker(s) active`
            });
        }

        if (criticalAlerts.length > 0) {
            issues.push({
                type: 'critical_alerts',
                severity: 'critical',
                count: criticalAlerts.length,
                message: `${criticalAlerts.length} critical alert(s) unresolved`
            });
        }

        if (totalLoss > 200) {
            issues.push({
                type: 'high_hourly_loss',
                severity: 'high',
                value: totalLoss,
                message: `Hourly loss of ${totalLoss.toFixed(2)} exceeds threshold`
            });

            // Create circuit breaker event
            await fetch(`${supabaseUrl}/rest/v1/circuit_breaker_events`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    breaker_type: 'max_loss_per_hour',
                    trigger_value: totalLoss,
                    threshold_value: 200.0,
                    description: `Hourly loss of ${totalLoss.toFixed(2)} exceeded threshold of 200`,
                    affected_operations: ['trading', 'autonomous_execution'],
                    resolved: false
                })
            });
        }

        if (consecutiveLosses >= 5) {
            issues.push({
                type: 'consecutive_losses',
                severity: 'high',
                value: consecutiveLosses,
                message: `${consecutiveLosses} consecutive losses detected`
            });

            // Create circuit breaker event
            await fetch(`${supabaseUrl}/rest/v1/circuit_breaker_events`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    breaker_type: 'max_consecutive_losses',
                    trigger_value: consecutiveLosses,
                    threshold_value: 5,
                    description: `${consecutiveLosses} consecutive losses exceeded threshold of 5`,
                    affected_operations: ['trading', 'autonomous_execution'],
                    resolved: false
                })
            });
        }

        if (lossRate > 0.5) {
            issues.push({
                type: 'high_loss_rate',
                severity: 'medium',
                value: lossRate,
                message: `Loss rate of ${(lossRate * 100).toFixed(1)}% exceeds 50%`
            });
        }

        // Generate system status report
        const systemStatus = {
            status: issues.length === 0 ? 'healthy' : 
                    issues.some(i => i.severity === 'critical') ? 'critical' : 'warning',
            timestamp: new Date().toISOString(),
            circuit_breakers_active: circuitBreakers.length,
            critical_alerts: criticalAlerts.length,
            recent_trades: recentTrades.length,
            recent_losses: recentLosses.length,
            total_hourly_loss: totalLoss,
            loss_rate: lossRate,
            consecutive_losses: consecutiveLosses,
            issues: issues
        };

        // Send notifications for critical issues
        if (issues.some(i => i.severity === 'critical')) {
            // Create notification (would be sent to all users or admins)
            await fetch(`${supabaseUrl}/rest/v1/notifications`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: null, // System-wide notification
                    type: 'system_error',
                    priority: 'critical',
                    title: 'Critical System Issues Detected',
                    body: `${issues.length} critical issue(s) require immediate attention`,
                    data: systemStatus
                })
            });
        }

        return new Response(JSON.stringify({ data: systemStatus }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Monitor system error:', error);

        const errorResponse = {
            error: {
                code: 'MONITOR_SYSTEM_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function calculateConsecutiveLosses(trades) {
    // Sort by created_at descending
    const sortedTrades = trades.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    let consecutive = 0;
    for (const trade of sortedTrades) {
        const profit = parseFloat(trade.actual_profit || trade.expected_profit || 0);
        if (profit < 0) {
            consecutive++;
        } else {
            break;
        }
    }

    return consecutive;
}
