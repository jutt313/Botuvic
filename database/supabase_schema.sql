-- ============================================
-- BOTUVIC - Supabase Database Schema
-- PostgreSQL 14+ with Row Level Security (RLS)
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- USERS TABLE (Extended Profile)
-- Note: Supabase auth.users() handles authentication
-- This table extends user data
-- ============================================
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    subscription_plan VARCHAR(20) NOT NULL DEFAULT 'free' 
        CHECK (subscription_plan IN ('free', 'pro', 'premium')),
    stripe_customer_id VARCHAR(255) UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_stripe_customer_id ON public.users(stripe_customer_id);
CREATE INDEX idx_users_subscription_plan ON public.users(subscription_plan);

-- RLS for users
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can read their own data
CREATE POLICY "Users can view own profile"
    ON public.users
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own data
CREATE POLICY "Users can update own profile"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id);

-- Users can insert their own profile (on signup)
CREATE POLICY "Users can insert own profile"
    ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ============================================
-- PROJECTS TABLE
-- ============================================
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tech_stack JSONB DEFAULT '[]'::jsonb,
    current_phase INTEGER DEFAULT 1 CHECK (current_phase > 0),
    total_phases INTEGER DEFAULT 1 CHECK (total_phases > 0),
    progress_percentage INTEGER DEFAULT 0 
        CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'paused', 'complete', 'archived')),
    project_data JSONB DEFAULT '{}'::jsonb,
    local_path VARCHAR(500),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for projects
CREATE INDEX idx_projects_user_id ON public.projects(user_id);
CREATE INDEX idx_projects_status ON public.projects(status);
CREATE INDEX idx_projects_created_at ON public.projects(created_at DESC);
CREATE INDEX idx_projects_tech_stack ON public.projects USING GIN(tech_stack);
CREATE INDEX idx_projects_project_data ON public.projects USING GIN(project_data);

-- RLS for projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Users can view their own projects
CREATE POLICY "Users can view own projects"
    ON public.projects
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own projects
CREATE POLICY "Users can create own projects"
    ON public.projects
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own projects
CREATE POLICY "Users can update own projects"
    ON public.projects
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own projects
CREATE POLICY "Users can delete own projects"
    ON public.projects
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- API KEYS TABLE
-- ============================================
CREATE TABLE public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL 
        CHECK (provider IN ('claude', 'openai', 'gemini', 'ollama', 'custom')),
    api_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Indexes for api_keys
CREATE INDEX idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX idx_api_keys_provider ON public.api_keys(provider);
CREATE INDEX idx_api_keys_is_default ON public.api_keys(user_id, is_default) WHERE is_default = TRUE;

-- RLS for api_keys
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Users can view their own API keys
CREATE POLICY "Users can view own API keys"
    ON public.api_keys
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own API keys
CREATE POLICY "Users can create own API keys"
    ON public.api_keys
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own API keys
CREATE POLICY "Users can update own API keys"
    ON public.api_keys
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own API keys
CREATE POLICY "Users can delete own API keys"
    ON public.api_keys
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- SUBSCRIPTIONS TABLE
-- ============================================
CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL 
        CHECK (plan IN ('free', 'pro', 'premium')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'cancelled', 'expired', 'past_due', 'trialing')),
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    cancelled_at TIMESTAMP,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_price_id VARCHAR(255),
    trial_end TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Indexes for subscriptions
CREATE INDEX idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON public.subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_current_period_end ON public.subscriptions(current_period_end);

-- RLS for subscriptions
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can view their own subscription
CREATE POLICY "Users can view own subscription"
    ON public.subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own subscription
CREATE POLICY "Users can create own subscription"
    ON public.subscriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own subscription
CREATE POLICY "Users can update own subscription"
    ON public.subscriptions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================
-- USAGE TRACKING TABLE
-- ============================================
CREATE TABLE public.usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL 
        CHECK (request_type IN ('scan', 'plan', 'generate', 'fix', 'chat', 'verify', 'other')),
    tokens_used INTEGER DEFAULT 0 CHECK (tokens_used >= 0),
    cost DECIMAL(10, 4) DEFAULT 0 CHECK (cost >= 0),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for usage_tracking
CREATE INDEX idx_usage_user_id ON public.usage_tracking(user_id);
CREATE INDEX idx_usage_project_id ON public.usage_tracking(project_id);
CREATE INDEX idx_usage_created_at ON public.usage_tracking(created_at DESC);
CREATE INDEX idx_usage_user_date ON public.usage_tracking(user_id, DATE(created_at));
CREATE INDEX idx_usage_provider ON public.usage_tracking(provider);

-- RLS for usage_tracking
ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;

-- Users can view their own usage
CREATE POLICY "Users can view own usage"
    ON public.usage_tracking
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own usage
CREATE POLICY "Users can insert own usage"
    ON public.usage_tracking
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- SESSIONS TABLE
-- ============================================
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for sessions
CREATE INDEX idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON public.sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON public.sessions(expires_at);
CREATE INDEX idx_sessions_last_used_at ON public.sessions(last_used_at DESC);

-- RLS for sessions
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

-- Users can view their own sessions
CREATE POLICY "Users can view own sessions"
    ON public.sessions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own sessions
CREATE POLICY "Users can insert own sessions"
    ON public.sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions"
    ON public.sessions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own sessions
CREATE POLICY "Users can delete own sessions"
    ON public.sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- SYNC LOGS TABLE
-- ============================================
CREATE TABLE public.sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL 
        CHECK (sync_type IN ('cli_to_cloud', 'cloud_to_cli', 'auto', 'manual')),
    status VARCHAR(20) NOT NULL 
        CHECK (status IN ('success', 'failed', 'partial', 'in_progress')),
    files_synced INTEGER DEFAULT 0 CHECK (files_synced >= 0),
    bytes_synced BIGINT DEFAULT 0 CHECK (bytes_synced >= 0),
    error_message TEXT,
    sync_duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for sync_logs
CREATE INDEX idx_sync_logs_user_id ON public.sync_logs(user_id);
CREATE INDEX idx_sync_logs_project_id ON public.sync_logs(project_id);
CREATE INDEX idx_sync_logs_created_at ON public.sync_logs(created_at DESC);
CREATE INDEX idx_sync_logs_status ON public.sync_logs(status);

-- RLS for sync_logs
ALTER TABLE public.sync_logs ENABLE ROW LEVEL SECURITY;

-- Users can view their own sync logs
CREATE POLICY "Users can view own sync logs"
    ON public.sync_logs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own sync logs
CREATE POLICY "Users can insert own sync logs"
    ON public.sync_logs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply triggers
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON public.projects
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at 
    BEFORE UPDATE ON public.api_keys
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at 
    BEFORE UPDATE ON public.subscriptions
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- FUNCTION: Auto-create user profile on signup
-- ============================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, email_verified, created_at)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.email_confirmed_at IS NOT NULL,
        NEW.created_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create user profile
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- FUNCTION: Clean up expired sessions
-- ============================================
CREATE OR REPLACE FUNCTION public.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.sessions
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTION: Get user's daily usage count
-- ============================================
CREATE OR REPLACE FUNCTION public.get_user_daily_usage(p_user_id UUID, p_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM public.usage_tracking
        WHERE user_id = p_user_id
        AND DATE(created_at) = p_date
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTION: Check if user has active subscription
-- ============================================
CREATE OR REPLACE FUNCTION public.has_active_subscription(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM public.subscriptions
        WHERE user_id = p_user_id
        AND status IN ('active', 'trialing')
        AND current_period_end > NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTION: Get user's current plan
-- ============================================
CREATE OR REPLACE FUNCTION public.get_user_plan(p_user_id UUID)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN (
        SELECT subscription_plan
        FROM public.users
        WHERE id = p_user_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTION: Check usage limit
-- ============================================
CREATE OR REPLACE FUNCTION public.check_usage_limit(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_plan VARCHAR(20);
    daily_usage INTEGER;
    usage_limit INTEGER;
BEGIN
    -- Get user plan
    user_plan := get_user_plan(p_user_id);
    
    -- Set limits based on plan
    CASE user_plan
        WHEN 'free' THEN usage_limit := 20;
        WHEN 'pro' THEN usage_limit := 1000;
        WHEN 'premium' THEN usage_limit := -1; -- unlimited
        ELSE usage_limit := 0;
    END CASE;
    
    -- If unlimited, return true
    IF usage_limit = -1 THEN
        RETURN TRUE;
    END IF;
    
    -- Get daily usage
    daily_usage := get_user_daily_usage(p_user_id);
    
    -- Check if under limit
    RETURN daily_usage < usage_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTION: Update project sync timestamp
-- ============================================
CREATE OR REPLACE FUNCTION public.update_project_sync_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.projects
    SET last_synced_at = NOW()
    WHERE id = NEW.project_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_sync_log_created
    AFTER INSERT ON public.sync_logs
    FOR EACH ROW
    WHEN (NEW.status = 'success')
    EXECUTE FUNCTION public.update_project_sync_timestamp();

-- ============================================
-- FUNCTION: Enforce single default API key per provider
-- ============================================
CREATE OR REPLACE FUNCTION public.enforce_single_default_api_key()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE public.api_keys
        SET is_default = FALSE
        WHERE user_id = NEW.user_id
        AND provider = NEW.provider
        AND id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER enforce_default_api_key
    AFTER INSERT OR UPDATE ON public.api_keys
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION public.enforce_single_default_api_key();

-- ============================================
-- VIEWS
-- ============================================

-- View: Active projects with user info
CREATE OR REPLACE VIEW public.active_projects_view AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.status,
    p.progress_percentage,
    p.current_phase,
    p.total_phases,
    p.tech_stack,
    p.created_at,
    p.updated_at,
    p.last_synced_at,
    u.email as user_email,
    u.name as user_name
FROM public.projects p
JOIN public.users u ON p.user_id = u.id
WHERE p.status = 'active';

-- View: User usage statistics
CREATE OR REPLACE VIEW public.user_usage_stats AS
SELECT 
    user_id,
    DATE(created_at) as usage_date,
    COUNT(*) as total_requests,
    SUM(tokens_used) as total_tokens,
    SUM(cost) as total_cost,
    COUNT(DISTINCT provider) as providers_used,
    SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful_requests,
    SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as failed_requests
FROM public.usage_tracking
GROUP BY user_id, DATE(created_at);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Composite indexes for common queries
CREATE INDEX idx_projects_user_status ON public.projects(user_id, status);
CREATE INDEX idx_usage_user_date_provider ON public.usage_tracking(user_id, DATE(created_at), provider);
CREATE INDEX idx_sync_logs_project_status ON public.sync_logs(project_id, status);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE public.users IS 'Extended user profiles linked to auth.users';
COMMENT ON TABLE public.projects IS 'User projects with metadata and progress tracking';
COMMENT ON TABLE public.api_keys IS 'Encrypted AI provider API keys';
COMMENT ON TABLE public.subscriptions IS 'User subscription and billing information';
COMMENT ON TABLE public.usage_tracking IS 'AI API usage tracking for billing and limits';
COMMENT ON TABLE public.sessions IS 'User session management for CLI and dashboard';
COMMENT ON TABLE public.sync_logs IS 'Project synchronization logs between CLI and cloud';

COMMENT ON FUNCTION public.handle_new_user() IS 'Auto-creates user profile on signup';
COMMENT ON FUNCTION public.cleanup_expired_sessions() IS 'Removes expired session tokens';
COMMENT ON FUNCTION public.get_user_daily_usage(UUID, DATE) IS 'Returns user daily API usage count';
COMMENT ON FUNCTION public.has_active_subscription(UUID) IS 'Checks if user has active subscription';
COMMENT ON FUNCTION public.check_usage_limit(UUID) IS 'Checks if user is within usage limits';

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant access to tables for authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Grant access to sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- Create a cleanup job (run this separately or schedule it)
-- SELECT cron.schedule('cleanup-sessions', '0 0 * * *', 'SELECT public.cleanup_expired_sessions();');

-- ============================================
-- SCHEMA COMPLETE
-- ============================================
-- Version: 1.0
-- Last Updated: 2024-01-15
-- Total Tables: 7
-- Total Functions: 7
-- Total Triggers: 5
-- Row Level Security: ENABLED on all tables
-- ============================================
