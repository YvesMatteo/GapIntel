-- Organizations Table
-- Groups users together for team features and API access

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_tier TEXT DEFAULT 'starter' CHECK (subscription_tier IN ('starter', 'pro', 'enterprise')),
    max_seats INT DEFAULT 1,
    max_api_calls_per_day INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team Members Table
-- Links users to organizations with roles

CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'revoked')),
    invited_by UUID REFERENCES auth.users(id),
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    UNIQUE(organization_id, email)
);

-- API Keys Table
-- For Enterprise API access

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,  -- First 8 chars for display: "gapi_abc..."
    key_hash TEXT NOT NULL,     -- SHA256 hash of full key
    scopes TEXT[] DEFAULT ARRAY['analyze', 'read'],
    calls_today INT DEFAULT 0,
    calls_total INT DEFAULT 0,
    last_call_at TIMESTAMPTZ,
    last_reset_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Organization Branding Table
-- For white-label reports

CREATE TABLE IF NOT EXISTS organization_branding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE UNIQUE,
    logo_url TEXT,
    primary_color TEXT DEFAULT '#7cffb2',
    secondary_color TEXT DEFAULT '#1a1a2e',
    accent_color TEXT DEFAULT '#b8b8ff',
    company_name TEXT,
    custom_footer_text TEXT,
    hide_gap_intel_branding BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update user_subscriptions to link to organizations
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_members_org ON team_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);

-- RLS Policies

-- Organizations: Owner and members can read
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own organizations" ON organizations
    FOR SELECT USING (
        owner_id = auth.uid() OR 
        id IN (SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND status = 'active')
    );

CREATE POLICY "Only owners can update organizations" ON organizations
    FOR UPDATE USING (owner_id = auth.uid());

CREATE POLICY "Authenticated users can create organizations" ON organizations
    FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Team Members: Org admins can manage
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Members can view their organization's team" ON team_members
    FOR SELECT USING (
        organization_id IN (
            SELECT id FROM organizations WHERE owner_id = auth.uid()
            UNION
            SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND status = 'active'
        )
    );

CREATE POLICY "Admins can manage team members" ON team_members
    FOR ALL USING (
        organization_id IN (
            SELECT id FROM organizations WHERE owner_id = auth.uid()
            UNION
            SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin' AND status = 'active'
        )
    );

-- API Keys: Org members can view, admins can manage
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Members can view API keys" ON api_keys
    FOR SELECT USING (
        organization_id IN (
            SELECT id FROM organizations WHERE owner_id = auth.uid()
            UNION
            SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND status = 'active'
        )
    );

CREATE POLICY "Admins can manage API keys" ON api_keys
    FOR ALL USING (
        organization_id IN (
            SELECT id FROM organizations WHERE owner_id = auth.uid()
            UNION
            SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin' AND status = 'active'
        )
    );

-- Branding: Org admins only
ALTER TABLE organization_branding ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can manage branding" ON organization_branding
    FOR ALL USING (
        organization_id IN (
            SELECT id FROM organizations WHERE owner_id = auth.uid()
            UNION
            SELECT organization_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin' AND status = 'active'
        )
    );

-- Service role can do everything
CREATE POLICY "Service role full access to organizations" ON organizations FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to team_members" ON team_members FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to api_keys" ON api_keys FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access to organization_branding" ON organization_branding FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Function to reset daily API call counts (run via cron)
CREATE OR REPLACE FUNCTION reset_daily_api_calls()
RETURNS void AS $$
BEGIN
    UPDATE api_keys 
    SET calls_today = 0, last_reset_at = NOW()
    WHERE last_reset_at < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to auto-create organization for new enterprise subscribers
CREATE OR REPLACE FUNCTION create_org_for_enterprise()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tier = 'enterprise' AND OLD.tier != 'enterprise' THEN
        INSERT INTO organizations (name, owner_id, subscription_tier, max_seats, max_api_calls_per_day)
        VALUES (
            COALESCE((SELECT email FROM auth.users WHERE id = NEW.user_id), 'Enterprise Org'),
            NEW.user_id,
            'enterprise',
            10,
            500
        )
        ON CONFLICT DO NOTHING;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create org on enterprise upgrade
DROP TRIGGER IF EXISTS trigger_create_org_for_enterprise ON user_subscriptions;
CREATE TRIGGER trigger_create_org_for_enterprise
    AFTER UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION create_org_for_enterprise();
