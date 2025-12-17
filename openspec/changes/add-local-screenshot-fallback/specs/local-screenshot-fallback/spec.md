# 本地截图文件备用方案规格

## ADDED Requirements

### Requirement: Local File System Fallback
The system **SHALL** provide local file system fallback when remote screenshot data is unavailable.

#### Scenario: Empty database screenshot data
- **WHEN** the database returns no screenshot data for a task
- **THEN** the system **SHALL** scan the local screenshots directory for matching files
- **AND** the system **SHALL** use file timestamps to match screenshots to task execution time
- **AND** the system **SHALL** return locally found screenshots as fallback data
- **AND** the fallback mechanism **SHALL** be transparent to the frontend

#### Scenario: Intelligent file matching
- **WHEN** scanning local screenshot files
- **THEN** the system **SHALL** parse screenshot filenames to extract timestamp information
- **AND** the system **SHALL** match files within a configurable time window of task execution
- **AND** the system **SHALL** prioritize files with timestamps closest to task execution time
- **AND** the system **SHALL** limit the number of returned files to prevent performance issues

#### Scenario: Path conversion and validation
- **WHEN** including local files in screenshot data
- **THEN** the system **SHALL** convert local file paths to web-accessible URLs
- **AND** the system **SHALL** validate that files exist before including them
- **AND** the system **SHALL** provide file metadata (size, timestamp) in the response
- **AND** invalid or missing files **SHALL** be filtered out gracefully

### Requirement: Multi-Source Data Aggregation
The system **SHALL** aggregate screenshot data from multiple sources with intelligent deduplication.

#### Scenario: Data source prioritization
- **WHEN** collecting screenshot data from multiple sources
- **THEN** the system **SHALL** prioritize data from step_screenshots table highest
- **AND** the system **SHALL** prioritize data from task_steps screenshot_path fields second
- **AND** the system **SHALL** use local file fallback as the lowest priority source
- **AND** the system **SHALL** maintain data source information for each screenshot

#### Scenario: Duplicate detection and removal
- **WHEN** aggregating screenshots from different sources
- **THEN** the system **SHALL** detect duplicate screenshots using file paths or URLs
- **AND** the system **SHALL** keep the highest priority source for duplicates
- **AND** the system **SHALL** preserve unique metadata from all sources
- **AND** duplicate removal **SHALL** not affect the original data sources

#### Scenario: Data integrity validation
- **WHEN** aggregating multi-source screenshot data
- **THEN** the system **SHALL** validate data structure consistency across sources
- **AND** the system **SHALL** ensure all screenshots have required fields (path/URL, timestamp)
- **AND** the system **SHALL** provide fallback values for missing optional fields
- **AND** invalid screenshot entries **SHALL** be logged and excluded

### Requirement: Performance Optimization
The local file fallback mechanism **SHALL** not significantly impact system performance.

#### Scenario: Caching and optimization
- **WHEN** repeatedly scanning local screenshot directories
- **THEN** the system **SHALL** implement caching for file scan results
- **AND** the system **SHALL** invalidate cache when directory contents change
- **AND** the system **SHALL** limit file scan operations to reasonable frequency
- **AND** caching **SHALL** be transparent to the API response

#### Scenario: Pagination and limiting
- **WHEN** returning local screenshot data
- **THEN** the system **SHALL** limit results to a maximum number of files (default 50)
- **AND** the system **SHALL** support pagination for large numbers of screenshots
- **AND** the system **SHALL** return the most relevant screenshots first
- **AND** performance metrics **SHALL** be logged for monitoring

#### Scenario: Asynchronous processing
- **WHEN** scanning local files might take significant time
- **THEN** the system **SHALL** implement asynchronous file scanning
- **AND** the system **SHALL** return partial results quickly when possible
- **AND** the system **SHALL** not block API responses for extended periods
- **AND** timeout protection **SHALL** prevent indefinite waiting

### Requirement: Error Handling and Resilience
The system **SHALL** handle local file system errors gracefully without affecting overall functionality.

#### Scenario: File system access errors
- **WHEN** encountering file system permission or access errors
- **THEN** the system **SHALL** log detailed error information for debugging
- **AND** the system **SHALL** continue with other available data sources
- **AND** the system **SHALL** return appropriate error metadata in the response
- **AND** file system errors **SHALL NOT** cause complete API failure

#### Scenario: File parsing and validation errors
- **WHEN** screenshot filenames cannot be parsed or are malformed
- **THEN** the system **SHALL** skip problematic files and continue processing
- **AND** the system **SHALL** log parsing errors with file details
- **AND** the system **SHALL** maintain overall screenshot data functionality
- **AND** individual file errors **SHALL NOT** affect other valid files

#### Scenario: Configuration and feature toggles
- **WHEN** local file fallback needs to be disabled or configured
- **THEN** the system **SHALL** support configuration options to enable/disable fallback
- **AND** the system **SHALL** allow configuration of time windows and file limits
- **AND** the system **SHALL** provide safe defaults for all configuration options
- **AND** configuration changes **SHALL** take effect without service restart

### Requirement: Comprehensive Logging and Monitoring
The system **SHALL** provide detailed logging for local file fallback operations.

#### Scenario: Operation tracking
- **WHEN** performing local file fallback operations
- **THEN** the system **SHALL** log the start and completion of file scans
- **AND** the system **SHALL** log the number of files found and matched
- **AND** the system **SHALL** log performance metrics for file operations
- **AND** log entries **SHALL** include task_id for correlation

#### Scenario: Debugging information
- **WHEN** local file fallback results in no matches
- **THEN** the system **SHALL** log detailed information about why no matches were found
- **AND** the system **SHALL** log the time windows used for matching
- **AND** the system **SHALL** log sample file timestamps for comparison
- **AND** debugging information **SHALL** be configurable by log level

#### Scenario: Quality metrics
- **WHEN** aggregating multi-source screenshot data
- **THEN** the system **SHALL** track the source of each screenshot in the response
- **AND** the system **SHALL** log statistics about data source usage
- **AND** the system **SHALL** monitor fallback success rates
- **AND** quality metrics **SHALL** be available for performance analysis