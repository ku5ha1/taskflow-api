-- Migration: Add soft delete columns and audit log table
-- Date: 2026-03-01

-- Add soft delete columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted);

-- Add soft delete columns to projects table
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_projects_is_deleted ON projects(is_deleted);

-- Add soft delete columns to tasks table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_tasks_is_deleted ON tasks(is_deleted);

-- Add soft delete columns to project_members table
ALTER TABLE project_members 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_project_members_is_deleted ON project_members(is_deleted);

-- Add timestamps to tasks if missing
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    username VARCHAR,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    endpoint VARCHAR(255)
);

-- Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record_id ON audit_logs(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
