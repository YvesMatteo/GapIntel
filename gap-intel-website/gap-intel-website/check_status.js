const { createClient } = require('@supabase/supabase-js');
// require('dotenv').config({ path: '.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase credentials');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkStatus() {
    const { data, error } = await supabase
        .from('analyses')
        .select('*')
        .eq('access_key', 'GAP-MQ0HKiRM37kP')
        .single();

    if (error) {
        console.error('Error fetching analysis:', error);
        return;
    }

    if (data) {
        console.log('Latest Analysis:');
        console.log(`Key: ${data.access_key}`);
        console.log(`Channel: ${data.channel_name}`);
        console.log(`Email: ${data.email}`);
        console.log(`Status: ${data.analysis_status}`);
        console.log(`Created At: ${data.created_at}`);

        if (data.analysis_result && data.analysis_result.error) {
            console.log(`Error Result: ${data.analysis_result.error}`);
        }
    } else {
        console.log('No analyses found');
    }
}

checkStatus();
