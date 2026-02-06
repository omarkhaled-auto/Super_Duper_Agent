-- =============================================================================
-- Bayan Database Initialization Script
-- PostgreSQL 16 Extensions and Initial Setup
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- Remove accents for search
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN indexes for JSONB

-- Create schemas
CREATE SCHEMA IF NOT EXISTS bayan;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS hangfire;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA bayan TO bayan_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO bayan_user;
GRANT ALL PRIVILEGES ON SCHEMA hangfire TO bayan_user;

-- Set default schema search path
ALTER DATABASE bayan SET search_path TO bayan, public;

-- Create audit function for automatic timestamp updates
CREATE OR REPLACE FUNCTION bayan.update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create function for generating reference codes
CREATE OR REPLACE FUNCTION bayan.generate_reference_code(prefix TEXT, seq_value BIGINT)
RETURNS TEXT AS $$
BEGIN
    RETURN prefix || '-' || TO_CHAR(CURRENT_DATE, 'YYMM') || '-' || LPAD(seq_value::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Bayan database initialized successfully at %', CURRENT_TIMESTAMP;
END
$$;
