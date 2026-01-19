---
description: Manage the Supabase database, apply schema updates, and run maintenance scripts.
---

# Manage Database

This workflow guides you through common database maintenance tasks using the SQL scripts located in `railway-api/premium/db/`.

## Steps

1. **List Available Scripts**
   See what SQL scripts are available for maintenance or schema updates.
   ```bash
   ls -la /Users/yvesromano/AiRAG/railway-api/premium/db/*.sql
   ```

2. **Apply Common Fixes**
   
   To fix **RLS (Row Level Security)** issues (e.g., frontend can't read data):
   > Go to Supabase SQL Editor and run `railway-api/premium/db/fix_org_rls.sql`.
   
   To **Optimize Performance**:
   > Go to Supabase SQL Editor and run `railway-api/premium/db/optimize_db.sql`.

   To **Reset/Fix General Supabase Config**:
   > Go to Supabase SQL Editor and run `railway-api/premium/db/supabase_fixes.sql`.

3. **Backup/Export Data**
   *(Optional)* If you need to verify data before acting, you can inspect the `analyses` table via the Supabase Table Editor.

## Important Note
This project uses **Supabase**. While you can run queries via `psql` if you have the connection string, it is often safer and easier to copy the content of the `.sql` files and execute them directly in the **Supabase Dashboard SQL Editor**.
