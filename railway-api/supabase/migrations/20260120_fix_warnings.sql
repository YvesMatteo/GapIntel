-- Create a new schema 'extensions' for better organization and security
CREATE SCHEMA IF NOT EXISTS extensions;

-- Make sure everyone can use it
GRANT USAGE ON SCHEMA extensions TO postgres, anon, authenticated, service_role;

-- Move the vector extension to the new schema
ALTER EXTENSION vector SET SCHEMA extensions;

-- Update the search path to include the new extensions schema
-- This ensures that functions from extensions are found without fully qualifying them
ALTER DATABASE postgres SET search_path TO public, extensions;

-- Also update for the current session to ensure immediate effect if run manually
SET search_path TO public, extensions;

-- Drop the duplicate index on ctr_training_data
-- The warning identified 'idx_ctr_training_date' and 'idx_ctr_training_fetch_date' as identical.
-- We will keep one and drop the other.
DROP INDEX IF EXISTS public.idx_ctr_training_fetch_date;
