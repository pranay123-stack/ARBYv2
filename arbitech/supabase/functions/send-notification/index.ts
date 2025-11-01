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
        const {
            user_id,
            notification_type,
            priority = 'medium',
            title,
            body,
            data = {},
            action_url = null
        } = await req.json();

        if (!user_id || !notification_type || !title || !body) {
            throw new Error('user_id, notification_type, title, and body are required');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Supabase configuration missing');
        }

        // Create notification record
        const notificationData = {
            user_id,
            type: notification_type,
            priority,
            title,
            body,
            data,
            action_url,
            sent_at: new Date().toISOString()
        };

        const response = await fetch(`${supabaseUrl}/rest/v1/notifications`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(notificationData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to create notification: ${errorText}`);
        }

        const savedNotification = await response.json();

        // In a production system, this would integrate with:
        // - Email service (SendGrid, AWS SES)
        // - SMS service (Twilio)
        // - Push notification service (Firebase, OneSignal)
        // - Webhook endpoints
        // - Discord/Slack webhooks
        // - Telegram bot API

        // For now, we log the notification
        console.log('Notification created:', {
            id: savedNotification[0].id,
            type: notification_type,
            priority,
            user_id
        });

        // Simulate delivery tracking
        const deliveryResult = {
            notification_id: savedNotification[0].id,
            delivered: true,
            channels_delivered: determineChannels(priority),
            delivery_timestamp: new Date().toISOString()
        };

        return new Response(JSON.stringify({
            data: {
                notification: savedNotification[0],
                delivery: deliveryResult
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Send notification error:', error);

        const errorResponse = {
            error: {
                code: 'SEND_NOTIFICATION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function determineChannels(priority) {
    // Determine which channels to use based on priority
    switch (priority) {
        case 'critical':
            return ['email', 'sms', 'push'];
        case 'high':
            return ['email', 'push'];
        case 'medium':
            return ['push'];
        case 'low':
            return ['push'];
        default:
            return ['push'];
    }
}
