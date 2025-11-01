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
        const { opportunity_id, user_id, processing_type } = await req.json();

        if (!opportunity_id) {
            throw new Error('opportunity_id is required');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Supabase configuration missing');
        }

        // Fetch opportunity with legs
        const oppResponse = await fetch(
            `${supabaseUrl}/rest/v1/arbitrage_opportunities?id=eq.${opportunity_id}`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        if (!oppResponse.ok) {
            throw new Error('Failed to fetch opportunity');
        }

        const opportunities = await oppResponse.json();
        if (opportunities.length === 0) {
            throw new Error('Opportunity not found');
        }

        const opportunity = opportunities[0];

        // Fetch legs
        const legsResponse = await fetch(
            `${supabaseUrl}/rest/v1/arbitrage_legs?opportunity_id=eq.${opportunity_id}`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        const legs = await legsResponse.json();

        // Process opportunity based on type
        let result = {};
        
        if (processing_type === 'risk_analysis') {
            // Calculate enhanced risk metrics
            const totalImpliedProb = legs.reduce((sum, leg) => 
                sum + parseFloat(leg.implied_probability), 0
            );
            
            const riskScore = totalImpliedProb > 1 ? 
                (totalImpliedProb - 1) * 100 : 0;
            
            result = {
                opportunity_id,
                risk_score: riskScore,
                total_implied_probability: totalImpliedProb,
                arbitrage_margin: 1 - totalImpliedProb,
                num_bookmakers: legs.length,
                timestamp: new Date().toISOString()
            };
            
            // Create risk alert if needed
            if (riskScore > 5) {
                await fetch(`${supabaseUrl}/rest/v1/risk_alerts`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'apikey': serviceRoleKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        alert_type: 'odds_discrepancy',
                        severity: 'medium',
                        title: 'High Risk Score Detected',
                        description: `Opportunity ${opportunity_id} has risk score ${riskScore.toFixed(2)}`,
                        opportunity_id,
                        user_id,
                        risk_metrics: result
                    })
                });
            }
            
        } else if (processing_type === 'validation') {
            // Validate opportunity data
            const validation_errors = [];
            
            if (parseFloat(opportunity.profit_margin) < 0.01) {
                validation_errors.push('Profit margin too low');
            }
            
            if (legs.length < 2) {
                validation_errors.push('Insufficient legs for arbitrage');
            }
            
            const now = new Date();
            const eventDate = new Date(opportunity.event_date);
            if (eventDate < now) {
                validation_errors.push('Event date in the past');
            }
            
            result = {
                opportunity_id,
                is_valid: validation_errors.length === 0,
                validation_errors,
                timestamp: new Date().toISOString()
            };
            
            // Update opportunity if errors found
            if (validation_errors.length > 0) {
                await fetch(
                    `${supabaseUrl}/rest/v1/arbitrage_opportunities?id=eq.${opportunity_id}`,
                    {
                        method: 'PATCH',
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            validation_errors
                        })
                    }
                );
            }
            
        } else {
            result = {
                opportunity_id,
                opportunity,
                legs,
                processed_at: new Date().toISOString()
            };
        }

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Process opportunity error:', error);

        const errorResponse = {
            error: {
                code: 'PROCESS_OPPORTUNITY_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
