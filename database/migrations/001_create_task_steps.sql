-- Migration 001: Create task_steps table
-- Description: Stores detailed information about each task execution step

-- Create task_steps table
CREATE TABLE IF NOT EXISTS task_steps (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    step_data JSONB NOT NULL,
    thinking TEXT,
    action_result JSONB,
    screenshot_path TEXT,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_task_steps_task_id
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_steps_task_id_step_number
    ON task_steps(task_id, step_number);

CREATE INDEX IF NOT EXISTS idx_task_steps_created_at
    ON task_steps(created_at);

CREATE INDEX IF NOT EXISTS idx_task_steps_step_type
    ON task_steps(step_type);

-- Add comments
COMMENT ON TABLE task_steps IS 'Stores detailed information about each task execution step';
COMMENT ON COLUMN task_steps.step_data IS 'JSON data containing step details';
COMMENT ON COLUMN task_steps.thinking IS 'AI model thinking process';
COMMENT ON COLUMN task_steps.action_result IS 'Result of the action execution';
COMMENT ON COLUMN task_steps.screenshot_path IS 'Path to screenshot file';
COMMENT ON COLUMN task_steps.duration_ms IS 'Step execution duration in milliseconds';