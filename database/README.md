# BOTUVIC Database Schema

## Overview

Complete PostgreSQL schema for Supabase with Row Level Security (RLS) enabled.

## Features Included

✅ **7 Tables** with proper relationships  
✅ **Row Level Security (RLS)** on all tables  
✅ **Auto-updated timestamps** via triggers  
✅ **Auto-create user profiles** on signup  
✅ **Helper functions** for common operations  
✅ **Indexes** for optimal performance  
✅ **JSONB** for flexible data storage  
✅ **Views** for common queries  
✅ **Constraints** for data integrity  

---

## Tables

### 1. **users**
Extended user profiles (linked to `auth.users`)
- User info, subscription plan, Stripe customer ID
- RLS: Users can only access their own data

### 2. **projects**
User projects with metadata
- Project name, description, tech stack (JSONB)
- Progress tracking, phases, status
- RLS: Users can only access their own projects

### 3. **api_keys**
Encrypted AI provider API keys
- Claude, OpenAI, Gemini, Ollama, custom
- Encrypted storage, one default per provider
- RLS: Users can only access their own keys

### 4. **subscriptions**
Subscription and billing data
- Plan (free/pro/premium), Stripe integration
- Period tracking, cancellation status
- RLS: Users can only view their own subscription

### 5. **usage_tracking**
AI API usage logs
- Request type, tokens used, cost
- Daily usage aggregation
- RLS: Users can only view their own usage

### 6. **sessions**
CLI and dashboard sessions
- Token management, device info
- Auto-cleanup of expired sessions
- RLS: Users can only manage their own sessions

### 7. **sync_logs**
CLI ↔ Dashboard sync history
- Sync type, status, files synced
- Error tracking
- RLS: Users can only view their own logs

---

## How to Apply Schema

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste the entire contents of `supabase_schema.sql`
5. Click **Run** (bottom right)
6. Wait for completion (should take ~5-10 seconds)

### Option 2: Supabase CLI

```bash
# Install Supabase CLI if needed
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Run the schema
supabase db push --file database/supabase_schema.sql
```

### Option 3: psql Command Line

```bash
psql "your-supabase-connection-string" -f database/supabase_schema.sql
```

---

## Verify Installation

After applying the schema, run this query to verify:

```sql
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Should return:
-- api_keys
-- projects
-- sessions
-- subscriptions
-- sync_logs
-- usage_tracking
-- users

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- All tables should have rowsecurity = true
```

---

## Key Functions

### `handle_new_user()`
Automatically creates user profile when user signs up via Supabase Auth.

### `cleanup_expired_sessions()`
Removes expired session tokens.
```sql
SELECT public.cleanup_expired_sessions();
```

### `get_user_daily_usage(user_id, date)`
Get user's daily API usage count.
```sql
SELECT public.get_user_daily_usage('user-uuid'::UUID, CURRENT_DATE);
```

### `has_active_subscription(user_id)`
Check if user has active subscription.
```sql
SELECT public.has_active_subscription('user-uuid'::UUID);
```

### `check_usage_limit(user_id)`
Check if user is within their usage limits.
```sql
SELECT public.check_usage_limit('user-uuid'::UUID);
```

---

## Row Level Security (RLS)

All tables have RLS enabled with these policies:

- **SELECT**: Users can only read their own data
- **INSERT**: Users can only create records for themselves
- **UPDATE**: Users can only update their own data
- **DELETE**: Users can only delete their own data

This means even if someone gets your database credentials, they can only access data for their authenticated user.

---

## Automatic Features

### Auto-create User Profile
When a user signs up via Supabase Auth, a profile is automatically created in the `users` table.

### Auto-update Timestamps
All tables with `updated_at` automatically update when a row is modified.

### Auto-sync Project Timestamp
When a successful sync log is created, the project's `last_synced_at` is automatically updated.

### Single Default API Key
Only one API key per provider can be set as default. Setting a new default automatically removes the flag from others.

---

## Sample Queries

### Get user's projects with progress
```sql
SELECT name, status, progress_percentage, current_phase, total_phases
FROM projects
WHERE user_id = auth.uid()
ORDER BY updated_at DESC;
```

### Get today's usage
```sql
SELECT COUNT(*), SUM(tokens_used), SUM(cost)
FROM usage_tracking
WHERE user_id = auth.uid()
AND DATE(created_at) = CURRENT_DATE;
```

### Get active API keys
```sql
SELECT provider, is_default, last_used_at
FROM api_keys
WHERE user_id = auth.uid()
AND is_active = TRUE;
```

### Get recent sync logs
```sql
SELECT project_id, sync_type, status, files_synced, created_at
FROM sync_logs
WHERE user_id = auth.uid()
ORDER BY created_at DESC
LIMIT 10;
```

---

## Migrations

If you need to modify the schema later, create migration files:

```bash
# Create a new migration
supabase migration new add_feature_name

# Edit the generated file in supabase/migrations/
# Then apply it
supabase db push
```

---

## Backup & Recovery

### Backup
```bash
# Using Supabase CLI
supabase db dump -f backup.sql

# Or using pg_dump
pg_dump "your-connection-string" > backup.sql
```

### Restore
```bash
psql "your-connection-string" < backup.sql
```

---

## Security Considerations

1. **Encryption**: API keys must be encrypted before storing in `api_keys.api_key_encrypted`
2. **RLS**: Always enabled - never disable in production
3. **Service Role**: Only use service role key for admin operations
4. **Anon Key**: Safe to use in frontend - RLS protects data
5. **Passwords**: Never stored - handled by Supabase Auth

---

## Performance Tips

1. **Indexes**: Already created for common queries
2. **JSONB**: Use for flexible data (tech_stack, project_data)
3. **Pagination**: Always use LIMIT and OFFSET for large results
4. **Connection Pooling**: Use Supabase's built-in pooler
5. **Cleanup**: Run `cleanup_expired_sessions()` daily via cron

---

## Troubleshooting

### RLS Errors
If you get "permission denied" errors:
- Make sure user is authenticated
- Check RLS policies are applied
- Verify `auth.uid()` matches row's `user_id`

### Migration Issues
If schema fails to apply:
- Check for syntax errors
- Apply sections incrementally
- Check Supabase logs for details

### Performance Issues
- Add indexes for frequently queried columns
- Use `EXPLAIN ANALYZE` to optimize queries
- Consider partitioning for large tables

---

## Next Steps

After applying the schema:

1. ✅ Test user signup → profile auto-creation
2. ✅ Create a test project
3. ✅ Add an API key (encrypted)
4. ✅ Track some usage
5. ✅ Test RLS by switching users

---

## Support

- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **RLS Guide**: https://supabase.com/docs/guides/auth/row-level-security

---

**Schema Version**: 1.0  
**PostgreSQL**: 14+  
**Supabase**: Compatible  
**Last Updated**: 2024-01-15
