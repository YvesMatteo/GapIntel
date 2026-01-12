-- Fix for infinite recursion in organizations RLS policy
-- The issue is that the INSERT policy checks team_members which has policies referencing organizations

-- Drop the restrictive INSERT policy
DROP POLICY IF EXISTS "Authenticated users can create organizations" ON organizations;

-- Create a simpler INSERT policy that just checks the user is authenticated and setting themselves as owner
CREATE POLICY "Users can create their own organizations" ON organizations
    FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND owner_id = auth.uid()
    );

-- Also fix the SELECT policy to avoid recursion
DROP POLICY IF EXISTS "Users can view their own organizations" ON organizations;

-- Simpler SELECT policy - just check ownership, team access handled by team_members table
CREATE POLICY "Users can view their organizations" ON organizations
    FOR SELECT USING (
        owner_id = auth.uid()
    );

-- Add a separate policy for team member access using a subquery that doesn't cause recursion
CREATE POLICY "Team members can view their organizations" ON organizations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM team_members tm 
            WHERE tm.organization_id = organizations.id 
            AND tm.user_id = auth.uid() 
            AND tm.status = 'active'
        )
    );
