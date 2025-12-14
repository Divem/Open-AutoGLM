-- Migration 004: Add screenshot URL fields for Supabase Storage integration
-- Description: Add fields to store Supabase Storage URLs alongside local paths

-- Add screenshot_url field to task_steps table
ALTER TABLE task_steps
ADD COLUMN IF NOT EXISTS screenshot_url TEXT;

-- Add comment
COMMENT ON COLUMN task_steps.screenshot_url IS 'Supabase Storage URL for the screenshot';

-- Add remote_url field to step_screenshots table
ALTER TABLE step_screenshots
ADD COLUMN IF NOT EXISTS remote_url TEXT;

-- Add comment
COMMENT ON COLUMN step_screenshots.remote_url IS 'Supabase Storage URL for the screenshot';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_task_steps_screenshot_url
    ON task_steps(screenshot_url)
    WHERE screenshot_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_step_screenshots_remote_url
    ON step_screenshots(remote_url)
    WHERE remote_url IS NOT NULL;

-- Function to update screenshot URLs for existing records
CREATE OR REPLACE FUNCTION update_screenshot_urls()
RETURNS TABLE(updated_records INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    -- This function can be called to migrate existing screenshots
    -- The actual migration will be done by the Python script

    RETURN QUERY SELECT 0 AS updated_records;
END;
$$;

-- Trigger to ensure at least one URL exists
CREATE OR REPLACE FUNCTION ensure_screenshot_url()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Ensure that if screenshot_path is null, screenshot_url is not null
    IF NEW.screenshot_path IS NULL AND NEW.screenshot_url IS NULL THEN
        RAISE EXCEPTION 'At least one of screenshot_path or screenshot_url must be provided';
    END IF;

    RETURN NEW;
END;
$$;

-- Apply trigger (commented out by default, can be enabled if needed)
-- CREATE TRIGGER ensure_screenshot_url_trigger
--     BEFORE INSERT OR UPDATE ON task_steps
--     FOR EACH ROW EXECUTE FUNCTION ensure_screenshot_url();