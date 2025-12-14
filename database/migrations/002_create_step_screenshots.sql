-- Migration 002: Create step_screenshots table
-- Description: Manages screenshots related to task steps

-- Create step_screenshots table
CREATE TABLE IF NOT EXISTS step_screenshots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id UUID NOT NULL,
    screenshot_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    compressed BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_step_screenshots_task_id
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_step_screenshots_step_id
        FOREIGN KEY (step_id) REFERENCES task_steps(id)
        ON DELETE CASCADE,

    -- Unique constraint to prevent duplicate screenshots
    CONSTRAINT uk_step_screenshots_path_hash
        UNIQUE (screenshot_path, file_hash)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_step_screenshots_task_id
    ON step_screenshots(task_id);

CREATE INDEX IF NOT EXISTS idx_step_screenshots_step_id
    ON step_screenshots(step_id);

CREATE INDEX IF NOT EXISTS idx_step_screenshots_file_hash
    ON step_screenshots(file_hash);

-- Add comments
COMMENT ON TABLE step_screenshots IS 'Manages screenshots related to task steps';
COMMENT ON COLUMN step_screenshots.screenshot_path IS 'Path to screenshot file';
COMMENT ON COLUMN step_screenshots.file_size IS 'File size in bytes';
COMMENT ON COLUMN step_screenshots.file_hash IS 'SHA256 hash of the file';
COMMENT ON COLUMN step_screenshots.compressed IS 'Whether the file is compressed';
COMMENT ON COLUMN step_screenshots.metadata IS 'Additional screenshot metadata';