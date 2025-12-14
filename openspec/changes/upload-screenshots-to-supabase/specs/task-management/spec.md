## ADDED Requirements

### Requirement: Screenshot Cloud Storage
The system SHALL upload task execution screenshots to Supabase Storage for remote access and persistence.

#### Scenario: Screenshot upload during task execution
- **WHEN** a screenshot is captured during task execution
- **THEN** the system SHALL upload it to Supabase Storage asynchronously
- **AND** store both local path and remote URL in the task step data

#### Scenario: Screenshot retrieval in task report
- **WHEN** viewing a task execution report
- **THEN** the system SHALL display screenshots from Supabase Storage URLs
- **AND** fallback to local files if remote URLs are unavailable

### Requirement: Screenshot Management Interface
The system SHALL provide a management interface for screenshots stored in Supabase.

#### Scenario: List screenshots for a task
- **WHEN** requesting screenshots for a specific task
- **THEN** the system SHALL return a list of screenshot URLs with timestamps
- **AND** support pagination for large sets

#### Scenario: Clean up old screenshots
- **WHEN** executing cleanup routine
- **THEN** the system SHALL delete screenshots older than configured retention period
- **AND** keep screenshots referenced by active tasks

#### Scenario: Batch upload existing screenshots
- **WHEN** migrating existing local screenshots
- **THEN** the system SHALL batch upload screenshots to Supabase Storage
- **AND** update task records with new URLs

## ADDED Requirements

### Requirement: Task-Step-Screenshot Database Integration
The system SHALL maintain database relationships between tasks, steps, and screenshots for proper data management and querying.

#### Scenario: Store screenshot metadata in database
- **WHEN** a screenshot is uploaded to Supabase
- **THEN** the system SHALL create a record in step_screenshots table
- **AND** store task_id, step_id, local_path, remote_url, file_size, and timestamp
- **AND** generate a unique screenshot ID for reference

#### Scenario: Query screenshots by task
- **WHEN** requesting all screenshots for a task
- **THEN** the system SHALL query step_screenshots table by task_id
- **AND** return ordered list of screenshots with step information
- **AND** include both local and remote URLs for fallback

#### Scenario: Link screenshot to specific step
- **WHEN** saving a task execution step
- **THEN** the system SHALL update task_steps.screenshot_url field
- **AND** maintain foreign key relationship in step_screenshots table
- **AND** ensure referential integrity between tables

## MODIFIED Requirements

### Requirement: Task Step Data Storage
The system SHALL store screenshot references in task step data for both local and remote storage with database persistence.

#### Scenario: Store screenshot with multiple references
- **WHEN** saving a task step with screenshot
- **THEN** the system SHALL store both local file path in screenshot_path field
- **AND** store Supabase URL in screenshot_url field in task_steps table
- **AND** create corresponding record in step_screenshots table
- **AND** mark the preferred source for display

#### Scenario: Load screenshot with fallback
- **WHEN** loading a task step screenshot
- **THEN** the system SHALL first check screenshot_url field in database
- **AND** attempt to load from Supabase URL if available
- **AND** fallback to screenshot_path (local) if remote is unavailable
- **AND** query step_screenshots table for additional metadata if needed