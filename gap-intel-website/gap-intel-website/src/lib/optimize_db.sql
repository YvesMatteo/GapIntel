-- OPTIMIZATION & CLEANUP SCRIPT
-- Run this to fix "Multiple Permissive Policies" and "Auth RLS Init Plan" warnings

-- 1. Drop ALL potential duplicate policies on report_folders
DROP POLICY IF EXISTS "Users can view own folders" ON report_folders;
DROP POLICY IF EXISTS "Users can view their own folders" ON report_folders;
DROP POLICY IF EXISTS "select_own_folders" ON report_folders;

DROP POLICY IF EXISTS "Users can create own folders" ON report_folders;
DROP POLICY IF EXISTS "Users can create their own folders" ON report_folders;
DROP POLICY IF EXISTS "insert_own_folders" ON report_folders;

DROP POLICY IF EXISTS "Users can update own folders" ON report_folders;
DROP POLICY IF EXISTS "Users can update their own folders" ON report_folders;
DROP POLICY IF EXISTS "update_own_folders" ON report_folders;

DROP POLICY IF EXISTS "Users can delete own folders" ON report_folders;
DROP POLICY IF EXISTS "Users can delete their own folders" ON report_folders;
DROP POLICY IF EXISTS "delete_own_folders" ON report_folders;

-- 2. Re-create Optimized Policies (using (select auth.uid()) for performance)

-- SELECT
CREATE POLICY "Users can view own folders" 
ON report_folders FOR SELECT 
TO authenticated 
USING (user_id = (select auth.uid()));

-- INSERT
CREATE POLICY "Users can create own folders" 
ON report_folders FOR INSERT 
TO authenticated 
WITH CHECK (user_id = (select auth.uid()));

-- UPDATE
CREATE POLICY "Users can update own folders" 
ON report_folders FOR UPDATE 
TO authenticated 
USING (user_id = (select auth.uid()))
WITH CHECK (user_id = (select auth.uid()));

-- DELETE
CREATE POLICY "Users can delete own folders" 
ON report_folders FOR DELETE 
TO authenticated 
USING (user_id = (select auth.uid()));
