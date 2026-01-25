# Manage Database

Manage the Supabase database, apply schema updates, and run maintenance scripts.

## Steps

1. **List Pending Scripts**
See what SQL scripts are available for maintenance or schema updates.
```bash
ls -la /Users/yvesromano/AiRAG/railway-api/premium/db/*.sql
```

2. **Apply Common Fixes**

To fix **RLS (Row Level Security)** issues:
```bash
python3 railway-api/scripts/db_manager.py --file /Users/yvesromano/AiRAG/railway-api/premium/db/fix_org_rls.sql
```

To **Optimize Performance**:
```bash
python3 railway-api/scripts/db_manager.py --file /Users/yvesromano/AiRAG/railway-api/premium/db/optimize_db.sql
```

To **Reset/Fix General Supabase Config**:
```bash
python3 railway-api/scripts/db_manager.py --file /Users/yvesromano/AiRAG/railway-api/premium/db/supabase_fixes.sql
```

3. **Verify Connection & Status**
Check that the database is accessible and responding.
```bash
python3 railway-api/scripts/db_manager.py --test
```
