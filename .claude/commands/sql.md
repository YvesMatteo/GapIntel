# SQL Manager

Execute SQL queries or files directly against the Supabase database. Acts as a "Supabase SQL Editor" for the agent.

## Usage

### Run a specific SQL file
```bash
python3 railway-api/scripts/db_manager.py --file /path/to/file.sql
```

### Run a raw SQL query
```bash
python3 railway-api/scripts/db_manager.py --query "SELECT * FROM users LIMIT 5;"
```

### Test Connection
```bash
python3 railway-api/scripts/db_manager.py --test
```

## Notes
- Always test connection before running queries
- Be careful with DELETE/UPDATE statements - verify with SELECT first
- Check RLS policies if you get permission errors
