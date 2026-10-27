-- Initialize database roles with forced RLS and least-privilege principles
-- Migrator role: owns tables, applies migrations, configures RLS policies
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'campuscare_migrator') THEN
    CREATE ROLE campuscare_migrator WITH LOGIN PASSWORD 'CampusCareMigrateSecurePass2026!';
  END IF;
END $$;

-- Runtime application role: NOBYPASSRLS, cannot bypass RLS
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'campuscare_app') THEN
    CREATE ROLE campuscare_app WITH LOGIN NOBYPASSRLS PASSWORD 'CampusCareAppSecurePass2026!';
  END IF;
END $$;

-- Grants for migrator
GRANT ALL PRIVILEGES ON DATABASE campuscare TO campuscare_migrator;
GRANT ALL ON SCHEMA public TO campuscare_migrator;

-- Grants for application role
GRANT CONNECT ON DATABASE campuscare TO campuscare_app;
GRANT USAGE ON SCHEMA public TO campuscare_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO campuscare_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO campuscare_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO campuscare_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO campuscare_app;
