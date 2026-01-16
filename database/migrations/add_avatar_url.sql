-- Migration: Add avatar_url to users table
-- Date: 2024-01-15

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

COMMENT ON COLUMN public.users.avatar_url IS 'URL to user profile avatar image';

