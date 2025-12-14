-- Migration 003: Extend tasks table with step statistics
-- Description: Add step-related statistics fields to tasks table

-- Add step statistics fields to tasks table
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS total_steps INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS successful_steps INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_steps INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_duration_ms INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_step_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS has_detailed_steps BOOLEAN DEFAULT false;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_tasks_has_detailed_steps
    ON tasks(has_detailed_steps);

CREATE INDEX IF NOT EXISTS idx_tasks_last_step_at
    ON tasks(last_step_at);

-- Add comments
COMMENT ON COLUMN tasks.total_steps IS 'Total number of steps in the task';
COMMENT ON COLUMN tasks.successful_steps IS 'Number of successful steps';
COMMENT ON COLUMN tasks.failed_steps IS 'Number of failed steps';
COMMENT ON COLUMN tasks.total_duration_ms IS 'Total execution duration in milliseconds';
COMMENT ON COLUMN tasks.last_step_at IS 'Timestamp of the last step';
COMMENT ON COLUMN tasks.has_detailed_steps IS 'Whether the task has detailed step data';