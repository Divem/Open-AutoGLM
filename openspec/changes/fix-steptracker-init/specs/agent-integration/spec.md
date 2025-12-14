# PhoneAgent StepTracker Integration Specification

## ADDED Requirements

### Requirement: StepTracker Initialization Timing
PhoneAgent **SHALL** initialize StepTracker only after task_id is available.

#### Scenario: StepTracker initialization in run() method
- **WHEN** PhoneAgent.run() is called and task_id is generated
- **THEN** StepTracker **SHALL** be initialized with the generated task_id
- **AND** initialization **SHALL** handle exceptions gracefully
- **AND** task execution **SHALL** continue even if StepTracker initialization fails

#### Scenario: Delayed StepTracker initialization
- **WHEN** PhoneAgent.__init__() is called
- **THEN** step_tracker attribute **SHALL** be initialized as None
- **AND** no StepTracker instance **SHALL** be created until task_id is available
- **AND** STEP_TRACKER_AVAILABLE check **SHALL** be deferred until initialization

### Requirement: Error Handling for StepTracker
StepTracker initialization and usage **SHALL** include comprehensive error handling.

#### Scenario: StepTracker initialization failure
- **WHEN** StepTracker constructor raises an exception
- **THEN** PhoneAgent **SHALL** log the error with a clear warning message
- **AND** step_tracker attribute **SHALL** remain None
- **AND** task execution **SHALL** continue without step tracking

#### Scenario: STEP_TRACKER_AVAILABLE is False
- **WHEN** StepTracker module cannot be imported
- **THEN** step_tracker attribute **SHALL** remain None
- **AND** no step tracking **SHALL** be attempted
- **AND** task execution **SHALL** proceed normally

## MODIFIED Requirements

### Requirement: Remove Non-Existent Method Calls
PhoneAgent **SHALL NOT** call non-existent methods on StepTracker.

#### Scenario: Eliminate start_task() call
- **WHEN** PhoneAgent.run() reaches step tracker initialization
- **THEN** any calls to step_tracker.start_task() **SHALL** be removed
- **AND** StepTracker **SHALL** be considered ready after successful initialization
- **AND** task_id **SHALL** be passed directly to the constructor

#### Scenario: Proper lifecycle management
- **WHEN** StepTracker is successfully initialized
- **THEN** it **SHALL** be ready to record steps immediately
- **AND** no additional setup methods **SHALL** be called
- **AND** step tracking **SHALL** work with the provided task_id