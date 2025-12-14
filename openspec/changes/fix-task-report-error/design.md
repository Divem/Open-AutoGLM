# Design: Fix Task Report Internal Server Error

## Context
The task report feature is experiencing 500 Internal Server Error when users click on the report button. This issue prevents users from viewing detailed execution information, including steps taken, screenshots captured, and success/failure statistics.

## Root Cause Analysis
1. **Database Schema Mismatch**: The code references a `remote_url` field in the `step_screenshots` table that may not exist in all database instances
2. **Insufficient Error Handling**: The code doesn't gracefully handle missing database fields or null values
3. **Frontend Vulnerability**: The JavaScript assumes all data will be present and properly formatted
4. **Missing Validation**: No startup validation to ensure database schema matches code expectations

## Goals / Non-Goals
- Goals:
  - Fix the 500 error and make task reports accessible
  - Implement robust error handling for partial data scenarios
  - Ensure graceful degradation when some data is missing
  - Provide clear feedback to users when issues occur
- Non-Goals:
  - Complete redesign of the reporting system
  - Adding new reporting features
  - Changing the database schema structure

## Decisions
- Decision: Implement defensive programming practices with field existence checks
  - Rationale: Prevents crashes due to schema differences between environments
  - Alternatives considered: Database schema auto-migration (too risky for production), Strict schema enforcement (would break existing instances)

- Decision: Add migration validation at application startup
  - Rationale: Early detection of schema issues prevents runtime errors
  - Alternatives considered: Runtime checks only (too late for users), Manual validation steps (error-prone)

- Decision: Use progressive enhancement for frontend display
  - Rationale: Ensures some information is always visible even with partial data
  - Alternatives considered: All-or-nothing display (poor UX), Silent failures (confusing)

## Risks / Trade-offs
- [Risk] Performance impact from additional validation checks
  - Mitigation: Cache validation results, use efficient queries
- [Risk] Masking underlying issues with too much error handling
  - Mitigation: Detailed logging for debugging, clear error messages
- [Trade-off] Increased code complexity for better reliability
  - Mitigation: Well-documented code, reusable validation utilities

## Migration Plan
1. Phase 1 - Immediate Fixes:
   - Add field existence checks in database access methods
   - Implement graceful error handling in report generation
   - Update frontend to handle missing data

2. Phase 2 - Validation Enhancement:
   - Add startup migration validation
   - Create migration verification tools
   - Update documentation

3. Phase 3 - Monitoring:
   - Add error tracking and alerting
   - Create health check endpoints
   - Monitor report generation success rates

## Implementation Details

### Database Access Layer
```python
def safe_get_field(record, field_name, default=None):
    """Safely get a field from a database record with fallback"""
    return record.get(field_name, default) if record else default
```

### Frontend Error Handling
```javascript
function safeDisplay(data, path, fallback) {
    // Safely navigate nested data structures
    // Return fallback if path doesn't exist
}
```

### Migration Validation
```python
def validate_step_screenshots_schema():
    """Verify required fields exist in step_screenshots table"""
    required_fields = ['id', 'task_id', 'step_id', 'screenshot_path']
    optional_fields = ['remote_url', 'file_size', 'file_hash']
    # Implementation details...
```

## Open Questions
- Should we implement automatic fallback queries for missing fields?
- How to handle database migrations in multi-tenant environments?
- What level of detail should be shown to users vs logged internally?

## Testing Strategy
- Unit tests for each defensive programming measure
- Integration tests with various database schema states
- End-to-end tests simulating error conditions
- Performance tests to validate impact of additional checks