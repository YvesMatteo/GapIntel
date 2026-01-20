const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Load env from .env.local
dotenv.config({ path: path.resolve(__dirname, '../.env.local') });

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function clean() {
    console.log('Cleaning stuck reports...');
    const { error } = await supabase
        .from('user_reports')
        .delete()
        .in('status', ['pending', 'processing']);

    if (error) {
        console.error('Error:', error);
        process.exit(1);
    } else {
        console.log("✅ Deleted stuck reports");
    }
}

clean();
