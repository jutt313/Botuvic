-- ============================================
-- BOTUVIC Schema Verification Tests
-- Run these queries after applying the schema
-- ============================================

-- Test 1: Verify all tables exist
SELECT 'Test 1: Tables Exist' as test_name;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'projects', 'api_keys', 'subscriptions', 'usage_tracking', 'sessions', 'sync_logs')
ORDER BY table_name;
-- Expected: 7 rows

-- Test 2: Verify RLS is enabled on all tables
SELECT 'Test 2: RLS Enabled' as test_name;
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'api_keys', 'subscriptions', 'usage_tracking', 'sessions', 'sync_logs');
-- Expected: All rows should have rowsecurity = true

-- Test 3: Verify all indexes exist
SELECT 'Test 3: Indexes Created' as test_name;
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'api_keys', 'subscriptions', 'usage_tracking', 'sessions', 'sync_logs')
ORDER BY indexname;
-- Expected: Multiple indexes

-- Test 4: Verify triggers exist
SELECT 'Test 4: Triggers Exist' as test_name;
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND event_object_table IN ('users', 'projects', 'api_keys', 'subscriptions');
-- Expected: 5 triggers (updated_at triggers + auth trigger + sync trigger + default key trigger)

-- Test 5: Verify functions exist
SELECT 'Test 5: Functions Exist' as test_name;
SELECT routine_name 
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_type = 'FUNCTION'
ORDER BY routine_name;
-- Expected: Multiple functions including handle_new_user, cleanup_expired_sessions, etc.

-- Test 6: Verify views exist
SELECT 'Test 6: Views Exist' as test_name;
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public';
-- Expected: active_projects_view, user_usage_stats

-- Test 7: Verify foreign key constraints
SELECT 'Test 7: Foreign Keys Exist' as test_name;
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
-- Expected: Multiple foreign key relationships

-- Test 8: Verify check constraints
SELECT 'Test 8: Check Constraints Exist' as test_name;
SELECT table_name, constraint_name
FROM information_schema.table_constraints
WHERE constraint_type = 'CHECK'
AND table_schema = 'public'
ORDER BY table_name;
-- Expected: Multiple check constraints

-- Test 9: Test helper functions
SELECT 'Test 9: Helper Functions Work' as test_name;

-- This will fail if no user exists yet, which is expected
-- SELECT public.get_user_daily_usage('00000000-0000-0000-0000-000000000000'::UUID);

-- Test cleanup function (should return 0 if no expired sessions)
SELECT public.cleanup_expired_sessions() as expired_sessions_cleaned;

-- Test 10: Verify JSONB columns
SELECT 'Test 10: JSONB Columns Exist' as test_name;
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND data_type = 'jsonb'
ORDER BY table_name, column_name;
-- Expected: tech_stack, project_data in projects; device_info in sessions

-- ============================================
-- Summary Query
-- ============================================
SELECT 'Schema Verification Summary' as summary;
SELECT 
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'projects', 'api_keys', 'subscriptions', 'usage_tracking', 'sessions', 'sync_logs')) as total_tables,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public') as total_triggers,
    (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public' AND routine_type = 'FUNCTION') as total_functions,
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') as total_views;

-- Expected Results:
-- total_tables: 7
-- total_indexes: 20+
-- total_triggers: 5+
-- total_functions: 7+
-- total_views: 2

-- ============================================
-- All tests complete!
-- ============================================
