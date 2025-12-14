# Database Persistence Specification

## MODIFIED Requirements

### Requirement: Supabase Authentication Configuration
Supabase **SHALL** use service_role key for database write operations.

#### Scenario: Correct key type for write operations
- **WHEN** Performing database write operations (INSERT, UPDATE, DELETE)
- **THEN** Supabase **SHALL** use service_role key
- **AND** publishable key **SHALL NOT** be used for write operations
- **AND** key **SHALL** have sufficient permissions for all required tables

#### Scenario: Key validation at startup
- **WHEN** SupabaseTaskManager is initialized
- **THEN** it **SHALL** validate key type and permissions
- **AND** log appropriate warnings for insufficient permissions
- **AND** provide clear error messages for invalid configurations

## ADDED Requirements

### Requirement: Database Schema Validation
The application **SHALL** validate database schema before attempting to save data.

#### Scenario: Required columns existence check
- **WHEN** Attempting to save step data
- **THEN** application **SHALL** verify task_steps table contains required columns
- **AND** columns **SHALL** include: step_id, task_id, step_number, step_type, step_data, thinking, created_at
- **AND** missing columns **SHALL** trigger migration or graceful degradation

#### Scenario: Foreign key constraint validation
- **WHEN** Saving screenshot data
- **THEN** task_id in step_screenshots **SHALL** exist in tasks table
- **AND** step_id **SHALL** reference valid step in task_steps table
- **AND** foreign key violations **SHALL** be logged and handled gracefully

### Requirement: Error Handling and Reporting
Database persistence operations **SHALL** include comprehensive error handling.

#### Scenario: Database save failure handling
- **WHEN** Database save operation fails
- **THEN** error **SHALL** be logged with detailed context
- **AND** task execution **SHALL** continue without interruption
- **AND** user **SHALL** be notified of persistence issues
- **AND** retry mechanism **SHALL** be implemented for transient errors

#### Scenario: Connection failure recovery
- **WHEN** Supabase connection is lost
- **THEN** application **SHALL** attempt to reconnect
- **AND** data **SHALL** be queued for later upload if possible
- **AND** connection status **SHALL** be displayed in the UI

### Requirement: Data Integrity Verification
Saved data **SHALL** maintain integrity and relationships.

#### Scenario: Step-screenshot relationship maintenance
- **WHEN** Saving step with screenshot
- **THEN** step_screenshots record **SHALL** correctly reference step_id
- **AND** screenshot file metadata **SHALL** be stored
- **AND** file hash **SHALL** be calculated and verified
- **AND** orphaned records **SHALL** be prevented

#### Scenario: Task completion data consistency
- **WHEN** Task is marked as completed
- **THEN** all related steps **SHALL** be saved to database
- **AND** step count **SHALL** match execution count
- **AND** final screenshots **SHALL** be associated with completion step

### Requirement: Migration Management
Database schema changes **SHALL** be managed through versioned migrations.

#### Scenario: Automatic migration detection
- **WHEN** Application starts
- **THEN** it **SHALL** check for pending migrations
- **AND** compare current schema version with expected version
- **AND** prompt or automatically run required migrations
- **AND** provide migration status feedback

#### Scenario: Migration rollback support
- **WHEN** Migration fails
- **THEN** system **SHALL** attempt to rollback changes
- **AND** maintain database in consistent state
- **AND** log detailed failure information
- **AND** provide manual recovery instructions