# Web UI Specification

## ADDED Requirements

### Requirement: Streamlined Screenshot Display
The system SHALL provide a single, optimized screenshot display mechanism through a floating window interface.

#### Scenario: Screenshot display consolidation
- **WHEN** user accesses the web interface
- **THEN** only the floating screenshot window is available for viewing screenshots
- **AND** no fixed screenshot panel exists in the sidebar

#### Scenario: Optimized sidebar space
- **WHEN** user views the web interface
- **THEN** the sidebar provides more space for device information, task history, and supported applications
- **AND** the layout remains balanced and visually appealing

## MODIFIED Requirements

### Requirement: Screenshot Toggle Control
The system SHALL provide a toggle control for screenshot visibility that exclusively manages the floating window.

#### Scenario: Toggle button interaction
- **WHEN** user clicks the screenshot toggle button or presses Ctrl+S
- **THEN** only the floating screenshot window visibility is affected
- **AND** the button provides clear visual feedback about the floating window state

#### Scenario: Keyboard shortcut
- **WHEN** user presses Ctrl+S
- **THEN** the floating screenshot window toggles visibility
- **AND** the fixed panel behavior is completely removed

## REMOVED Requirements

### Requirement: Fixed Screenshot Panel
**Reason**: The fixed screenshot panel creates redundancy with the floating window and consumes valuable sidebar space. The floating window provides superior flexibility and user experience.

**Migration**: Users will seamlessly transition to the floating window interface which offers enhanced features including dragging, resizing, and always-on-top capability.

#### Scenario: Panel removal
- **REMOVED** Fixed screenshot panel in the sidebar
- **REMOVED** Static screenshot container within the sidebar
- **REMOVED** Associated CSS styles for fixed panel layout

### Requirement: Dual Screenshot Display Modes
**Reason**: Having two simultaneous screenshot display modes creates confusion and inefficient use of screen real estate.

**Migration**: All screenshot functionality is consolidated into the floating window, providing a consistent and improved user experience.

#### Scenario: Mode consolidation
- **REMOVED** Option to view screenshots in both fixed panel and floating window
- **REMOVED** Logic for managing two separate display states