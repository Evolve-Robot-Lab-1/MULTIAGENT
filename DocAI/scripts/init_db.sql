-- Create DocAI database schema initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer');
CREATE TYPE document_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Grant permissions to docai user
GRANT ALL PRIVILEGES ON DATABASE docai TO docai;
GRANT ALL ON SCHEMA public TO docai;

-- Create indexes for better performance
-- These will be created after tables are created by Alembic migrations

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create initial configuration table
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO system_config (key, value, description) VALUES
    ('version', '2.0.0', 'System version'),
    ('maintenance_mode', 'false', 'Enable/disable maintenance mode'),
    ('max_upload_size', '52428800', 'Maximum file upload size in bytes'),
    ('session_timeout', '86400', 'Session timeout in seconds'),
    ('rag_enabled', 'true', 'Enable RAG functionality')
ON CONFLICT (key) DO NOTHING;

-- Create trigger for system_config
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE
    ON system_config FOR EACH ROW EXECUTE PROCEDURE 
    update_updated_at_column();