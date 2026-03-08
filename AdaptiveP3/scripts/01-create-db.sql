-- Create database and role for AP3
-- Run this against the default 'postgres' database as a superuser.

-- Create a dedicated role (optional but recommended)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ap3_user') THEN
        CREATE ROLE ap3_user LOGIN PASSWORD 'ap3_password';
    END IF;
END
$$;

-- Create the database if it does not exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ap3_db') THEN
        CREATE DATABASE ap3_db OWNER ap3_user;
    END IF;
END
$$;
