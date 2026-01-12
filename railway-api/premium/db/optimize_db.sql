-- SECURITY & OPTIMIZATION MIGRATION SCRIPT v8
-- Addresses final Multiple Permissive Policies warning by consolidating subscriptions policy

-- 1. HELPER FUNCTION (Performance)
-- We wrap the email extraction in a STABLE function. 
-- This guarantees Postgres evaluates it only once per query (InitPlan), not per row.
CREATE OR REPLACE FUNCTION get_auth_email()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT nullif(current_setting('request.jwt.claim.email', true), '');
$$;

-- 2. FIX ANALYSES RLS
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Authenticated insert allowed" ON public.analyses;

CREATE POLICY "Authenticated insert allowed" ON public.analyses
    FOR INSERT TO authenticated
    WITH CHECK (
        email = (SELECT get_auth_email())
    );

-- 3. FIX USER SUBSCRIPTIONS RLS
-- Consolidate back to single policy to fix "Multiple Permissive Policies" warning
-- But use STABLE function + subquery wrapper to avoid "InitPlan" warning.

DROP POLICY IF EXISTS "Users can view own subscriptions" ON user_subscriptions;
DROP POLICY IF EXISTS "Users can view own subscriptions by id" ON user_subscriptions;
DROP POLICY IF EXISTS "Users can view own subscriptions by email" ON user_subscriptions;

CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT TO authenticated
    USING (
        user_id = (SELECT auth.uid()) 
        OR 
        user_email = (SELECT get_auth_email())
    );
