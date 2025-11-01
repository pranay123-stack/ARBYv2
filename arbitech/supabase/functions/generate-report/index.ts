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
        const { user_id, period_days = 7 } = await req.json();

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Supabase configuration missing');
        }

        // Calculate date range
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - period_days);

        // Build query filter
        const dateFilter = `created_at=gte.${startDate.toISOString()}&created_at=lte.${endDate.toISOString()}`;
        const userFilter = user_id ? `&user_id=eq.${user_id}` : '';

        // Fetch trades
        const tradesResponse = await fetch(
            `${supabaseUrl}/rest/v1/trades?${dateFilter}${userFilter}`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        if (!tradesResponse.ok) {
            throw new Error('Failed to fetch trades');
        }

        const trades = await tradesResponse.json();

        // Calculate metrics
        const totalTrades = trades.length;
        const successfulTrades = trades.filter(t => t.status === 'settled' || t.status === 'filled').length;
        const failedTrades = trades.filter(t => t.status === 'failed').length;
        
        const totalProfit = trades.reduce((sum, t) => {
            const profit = parseFloat(t.actual_profit || t.expected_profit || 0);
            return sum + profit;
        }, 0);

        const totalLoss = trades.reduce((sum, t) => {
            const profit = parseFloat(t.actual_profit || t.expected_profit || 0);
            return sum + (profit < 0 ? Math.abs(profit) : 0);
        }, 0);

        const avgExecutionTime = trades.length > 0 ? 
            trades.reduce((sum, t) => sum + (t.execution_time_ms || 0), 0) / trades.length : 0;

        const winRate = totalTrades > 0 ? successfulTrades / totalTrades : 0;
        const avgProfitPerTrade = totalTrades > 0 ? totalProfit / totalTrades : 0;

        // Calculate max drawdown
        let maxDrawdown = 0;
        let peak = 0;
        let runningProfit = 0;
        
        for (const trade of trades) {
            const profit = parseFloat(trade.actual_profit || trade.expected_profit || 0);
            runningProfit += profit;
            
            if (runningProfit > peak) {
                peak = runningProfit;
            }
            
            const drawdown = peak - runningProfit;
            if (drawdown > maxDrawdown) {
                maxDrawdown = drawdown;
            }
        }

        // Calculate volatility (standard deviation of profits)
        const profits = trades.map(t => parseFloat(t.actual_profit || t.expected_profit || 0));
        const avgProfit = profits.reduce((sum, p) => sum + p, 0) / profits.length;
        const variance = profits.reduce((sum, p) => sum + Math.pow(p - avgProfit, 2), 0) / profits.length;
        const volatility = Math.sqrt(variance);

        // Calculate Sharpe ratio (simplified: avgProfit / volatility)
        const sharpeRatio = volatility > 0 ? avgProfit / volatility : 0;

        const metricsData = {
            user_id: user_id || null,
            period_start: startDate.toISOString(),
            period_end: endDate.toISOString(),
            total_trades: totalTrades,
            successful_trades: successfulTrades,
            failed_trades: failedTrades,
            total_profit: totalProfit,
            total_loss: totalLoss,
            net_profit: totalProfit - totalLoss,
            win_rate: winRate,
            avg_profit_per_trade: avgProfitPerTrade,
            avg_execution_time_ms: Math.round(avgExecutionTime),
            sharpe_ratio: sharpeRatio,
            max_drawdown: maxDrawdown,
            volatility: volatility
        };

        // Save metrics to database
        const saveResponse = await fetch(`${supabaseUrl}/rest/v1/performance_metrics`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(metricsData)
        });

        if (!saveResponse.ok) {
            console.error('Failed to save metrics:', await saveResponse.text());
        }

        const savedMetrics = await saveResponse.json();

        return new Response(JSON.stringify({
            data: {
                metrics: metricsData,
                saved: savedMetrics.length > 0,
                trades_analyzed: totalTrades,
                report_generated_at: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Generate report error:', error);

        const errorResponse = {
            error: {
                code: 'GENERATE_REPORT_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
