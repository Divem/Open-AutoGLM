## 1. Database Schema Extensions
**PREREQUISITE**: add-task-step-persistence must be implemented first

- [x] 1.1 Configure AutoGLMStorage bucket access policies
  - Set public read access for screenshots
  - Configure authenticated upload permissions
- [x] 1.2 Add screenshot_url field to task_steps table
  - ALTER TABLE task_steps ADD COLUMN screenshot_url TEXT
  - Keep existing screenshot_path field for backward compatibility
- [x] 1.3 Add remote_url field to step_screenshots table
  - ALTER TABLE step_screenshots ADD COLUMN remote_url TEXT
  - Store Supabase Storage URL here
- [x] 1.4 Create additional indexes for Supabase queries
  - idx_step_screenshots_remote_url (remote_url)
  - idx_task_steps_screenshot_url (screenshot_url)
- [x] 1.5 Document storage configuration in environment variables

## 2. Screenshot Upload Service
- [x] 2.1 Create ScreenshotManager class in supabase_manager.py
  - Use AutoGLMStorage bucket configuration
  - Integrate with database operations
- [x] 2.2 Implement async upload function with retry logic
  - Update database with upload status
  - Store both local and remote URLs
- [x] 2.3 Add compression optimization before upload
- [x] 2.4 Implement batch upload for existing screenshots
  - Update database records with new URLs
- [x] 2.5 Add error handling and logging
  - Include Supabase Storage error codes handling
  - Log database operation failures

## 3. Integration with Task Execution
- [x] 3.1 Modify phone_agent/adb/screenshot.py to trigger upload
  - Enhanced screenshot function to save to web directory
  - Added automatic upload trigger
- [x] 3.2 Update task step saving workflow
  - Save step data to task_steps table
  - Create records in step_screenshots table
  - Include both local and remote URLs
- [x] 3.3 Ensure backward compatibility with local paths
- [x] 3.4 Add upload status tracking in database
  - Track upload progress per screenshot
  - Handle failed uploads gracefully

## 4. Web Interface Updates
- [x] 4.1 Update web/app.py to serve screenshots from database
  - Query task_steps for screenshot URLs
  - Query step_screenshots for metadata
  - Serve from Supabase URLs with local fallback
- [x] 4.2 Add fallback mechanism for local files
- [x] 4.3 Implement screenshot loading progress indicator
- [x] 4.4 Update screenshot display in task reports
  - Show screenshots grouped by step
  - Display timestamps and metadata
  - Show cloud indicator for remote URLs
- [x] 4.5 Add API endpoints for screenshot management
  - GET /tasks/{task_id}/screenshots
  - GET /steps/{step_id}/screenshots
  - POST /screenshots/upload (batch upload)

## 5. Frontend Updates
- [x] 5.1 Modify app.js to handle Supabase screenshot URLs
  - Prefer remote URLs over local paths
  - Show cloud indicator for uploaded screenshots
- [x] 5.2 Add lazy loading for screenshots
- [x] 5.3 Implement screenshot preview modal
- [x] 5.4 Update error handling for failed loads

## 6. Management Utilities
- [x] 6.1 Create CLI command for screenshot cleanup
  - Clean old records from step_screenshots table
  - Remove orphaned files from Supabase Storage
- [x] 6.2 Implement retention policy configuration
  - Database-level retention policies
  - Storage bucket lifecycle rules
- [x] 6.3 Add screenshot statistics reporting
  - Query database for storage usage stats
  - Report per-task screenshot counts
- [x] 6.4 Create migration utility for existing screenshots
  - Scan local screenshots directory
  - Bulk upload to Supabase Storage
  - Update database records with new URLs
- [x] 6.5 Add database consistency checks
  - Verify step_screenshots records match files
  - Fix broken references
  - Clean up duplicate entries

## 7. Testing and Validation
- [x] 7.1 Unit tests for ScreenshotManager
- [x] 7.2 Integration tests for upload workflow
- [x] 7.3 Test database operations
  - Test task_steps and step_screenshots CRUD
  - Test foreign key constraints
  - Test data consistency
- [x] 7.4 Test fallback mechanisms
- [x] 7.5 Performance testing with large screenshot sets
- [x] 7.6 Validate cleanup routines
- [x] 7.7 Test API endpoints for screenshot management

## 8. Documentation
- [x] 8.1 Update API documentation
  - Document new database schema
  - Document screenshot endpoints
- [x] 8.2 Add troubleshooting guide
  - Database connection issues
  - Upload failure scenarios
- [x] 8.3 Document configuration options
  - Database schema settings
  - Storage configuration variables
- [x] 8.4 Create migration guide
  - From local-only to hybrid storage
  - Database migration steps