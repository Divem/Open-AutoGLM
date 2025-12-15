# Data Reporting Specification

## ADDED Requirements

### Requirement: Task Execution Data Persistence
Task execution steps **SHALL** be persistently stored to database for reporting.

#### Scenario: Step data保存 during task execution
- **WHEN** A task step is executed via step_callback
- **THEN** step data **SHALL** be saved to task_steps table
- **AND** step data **SHALL** include all relevant fields (task_id, step_number, step_type, etc.)
- **AND** saving status **SHALL** be logged for debugging
- **AND** save failures **SHALL NOT** interrupt task execution

#### Scenario: Screenshot metadata保存
- **WHEN** A step produces a screenshot
- **THEN** screenshot metadata **SHALL** be saved to step_screenshots table
- **AND** screenshot **SHALL** be linked to corresponding step via step_id
- **AND** file metadata (size, hash, path) **SHALL** be recorded
- **AND** save operation **SHALL** be atomic and consistent

### Requirement: Statistical API Endpoints
The application **SHALL** provide REST API endpoints for accessing task statistics.

#### Scenario: Overall statistics endpoint
- **WHEN** Client requests GET /api/statistics
- **THEN** endpoint **SHALL** return aggregated task statistics
- **AND** response **SHALL** include task counts by status
- **AND** response **SHALL** include step and screenshot counts
- **AND** response **SHALL** include success/failure ratios
- **AND** endpoint **SHALL** handle time range queries

#### Scenario: Task summary endpoint
- **WHEN** Client requests GET /api/tasks/summary
- **THEN** endpoint **SHALL** return task execution summary
- **AND** response **SHALL** include daily/weekly/monthly trends
- **AND** response **SHALL** include performance metrics
- **AND** response **SHALL** be properly formatted for charts

### Requirement: Data Validation and Integrity
Reported data **SHALL** accurately reflect database state.

#### Scenario: Data consistency validation
- **WHEN** Generating reports
- **THEN** reported counts **SHALL** match database table counts
- **AND** task-step relationships **SHALL** be properly maintained
- **AND** orphaned records **SHALL** be detected and handled
- **AND** data integrity **SHALL** be validated before display

#### Scenario: Real-time data updates
- **WHEN** New tasks are completed
- **THEN** statistics **SHALL** be updated in real-time
- **AND** cache **SHALL** be invalidated appropriately
- **AND** clients **SHALL** receive updated data via WebSocket or polling
- **AND** stale data **SHALL NOT** be displayed

## MODIFIED Requirements

### Requirement: Supabase Integration Detection
Supabase availability **SHALL** be correctly detected and utilized.

#### Scenario: Availability check at startup
- **WHEN** Application initializes
- **THEN** SUPABASE_AVAILABLE **SHALL** be set based on actual connection test
- **AND** false positives/negatives **SHALL** be avoided
- **AND** connection status **SHALL** be logged
- **AND** graceful degradation **SHALL** occur if unavailable

#### Scenario: Runtime availability validation
- **WHEN** Attempting database operations
- **THEN** availability **SHALL** be re-validated if previous operations failed
- **AND** retry mechanism **SHALL** be implemented for transient failures
- **AND** fallback behavior **SHALL** be clearly documented
- **AND** user **SHALL** be notified of unavailability