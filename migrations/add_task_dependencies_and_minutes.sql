-- Add estimated_minutes and actual_minutes to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_minutes INTEGER;

-- Create task_dependencies table
CREATE TABLE IF NOT EXISTS task_dependencies (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'blocks',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_task_dependency UNIQUE (task_id, depends_on_task_id),
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_type ON task_dependencies(dependency_type);
