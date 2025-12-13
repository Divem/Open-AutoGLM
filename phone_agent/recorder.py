"""
Script recorder for Phone Agent - records and generates automation scripts.
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ScriptStep:
    """Represents a single step in the automation script."""
    step_number: int
    action_type: str
    action_data: Dict[str, Any]
    thinking: str
    screenshot_path: Optional[str] = None
    timestamp: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ScriptMetadata:
    """Metadata for the automation script."""
    task_name: str
    description: str
    created_at: str
    total_steps: int
    device_id: Optional[str] = None
    model_name: Optional[str] = None
    success_rate: Optional[float] = None
    execution_time: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ScriptRecorder:
    """
    Records Phone Agent actions and generates automation scripts.

    This class captures all actions performed by the Phone Agent,
    along with context information, and can export them as replayable scripts.
    """

    def __init__(self, output_dir: str = "scripts"):
        """
        Initialize the script recorder.

        Args:
            output_dir: Directory to save generated scripts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.steps: List[ScriptStep] = []
        self.metadata: Optional[ScriptMetadata] = None
        self.start_time: Optional[float] = None
        self.screenshot_dir = self.output_dir / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

    def start_recording(self, task: str, device_id: Optional[str] = None,
                       model_name: Optional[str] = None):
        """
        Start recording a new task.

        Args:
            task: Task description
            device_id: Device identifier
            model_name: Model name used
        """
        self.steps = []
        self.start_time = time.time()
        self.metadata = ScriptMetadata(
            task_name=task[:50] + "..." if len(task) > 50 else task,
            description=task,
            created_at=datetime.now().isoformat(),
            total_steps=0,
            device_id=device_id,
            model_name=model_name
        )

    def record_step(self, action: Dict[str, Any], thinking: str,
                   success: bool = True, error_message: Optional[str] = None,
                   screenshot_base64: Optional[str] = None):
        """
        Record a single step in the automation.

        Args:
            action: The action dictionary
            thinking: AI thinking process
            success: Whether the step was successful
            error_message: Error message if step failed
            screenshot_base64: Base64 encoded screenshot
        """
        step_number = len(self.steps) + 1
        screenshot_path = None

        # Save screenshot if provided
        if screenshot_base64:
            screenshot_path = self._save_screenshot(screenshot_base64, step_number)

        step = ScriptStep(
            step_number=step_number,
            action_type=action.get("action", "unknown"),
            action_data=action,
            thinking=thinking,
            screenshot_path=screenshot_path,
            success=success,
            error_message=error_message
        )

        self.steps.append(step)

        # Update metadata
        if self.metadata:
            self.metadata.total_steps = len(self.steps)

    def _save_screenshot(self, base64_data: str, step_number: int) -> str:
        """
        Save screenshot to file.

        Args:
            base64_data: Base64 encoded image data
            step_number: Current step number

        Returns:
            Path to saved screenshot
        """
        import base64

        try:
            # Extract the base64 part (remove data:image/...;base64, prefix if present)
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            image_data = base64.b64decode(base64_data)
            screenshot_path = self.screenshot_dir / f"step_{step_number:03d}.png"

            with open(screenshot_path, 'wb') as f:
                f.write(image_data)

            return str(screenshot_path.relative_to(self.output_dir))
        except Exception as e:
            print(f"Warning: Failed to save screenshot for step {step_number}: {e}")
            return None

    def finish_recording(self, success: bool = True):
        """
        Finish recording and update metadata.

        Args:
            success: Whether the overall task was successful
        """
        if self.metadata and self.start_time:
            execution_time = time.time() - self.start_time
            self.metadata.execution_time = round(execution_time, 2)

            # Calculate success rate
            successful_steps = sum(1 for step in self.steps if step.success)
            self.metadata.success_rate = round(successful_steps / len(self.steps) * 100, 2) if self.steps else 0

    def generate_script(self) -> Dict[str, Any]:
        """
        Generate the complete script data.

        Returns:
            Dictionary containing the complete script
        """
        return {
            "metadata": asdict(self.metadata) if self.metadata else {},
            "steps": [asdict(step) for step in self.steps]
        }

    def save_script(self, filename: Optional[str] = None) -> str:
        """
        Save the script to a JSON file.

        Args:
            filename: Optional filename. If not provided, generates one based on timestamp.

        Returns:
            Path to saved script file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_name = self.metadata.task_name.replace(" ", "_").replace("/", "_")[:20] if self.metadata else "task"
            filename = f"{timestamp}_{task_name}.json"

        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'

        script_path = self.output_dir / filename

        script_data = self.generate_script()

        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        return str(script_path)

    def generate_python_script(self, json_filename: str) -> str:
        """
        Generate a Python script that can replay the recorded actions.

        Args:
            json_filename: The JSON script file to load data from

        Returns:
            Path to generated Python script
        """
        script_name = Path(json_filename).stem + '_replay.py'
        script_path = self.output_dir / script_name

        python_code = f'''#!/usr/bin/env python3
"""
Auto-generated replay script for Phone Agent task.
Generated on: {datetime.now().isoformat()}

To run this script:
    python {script_name}

Requirements:
    - phone_agent package
    - PIL (for screenshots if needed)
"""

import json
import sys
import time
from pathlib import Path

# Add the parent directory to the path to import phone_agent
sys.path.append(str(Path(__file__).parent.parent.parent))

from phone_agent.adb import launch_app, tap, type_text, swipe, back, home
from phone_agent.adb.input import clear_text, detect_and_set_adb_keyboard, restore_keyboard


class ReplayScript:
    """Replay script for Phone Agent automation."""

    def __init__(self, json_file: str):
        """
        Initialize the replay script.

        Args:
            json_file: Path to the JSON script file
        """
        self.json_file = Path(json_file)
        self.script_data = self._load_script()
        self.metadata = self.script_data.get("metadata", {{}})
        self.steps = self.script_data.get("steps", [])

    def _load_script(self) -> dict:
        """Load the script data from JSON file."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Script file not found: {{self.json_file}}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in script file: {{e}}")
            sys.exit(1)

    def print_info(self):
        """Print script information."""
        print("=" * 60)
        print("📱 Phone Agent Replay Script")
        print("=" * 60)
        task_name = self.metadata.get('task_name', 'Unknown')
        description = self.metadata.get('description', 'No description')
        total_steps = self.metadata.get('total_steps', 0)
        success_rate = self.metadata.get('success_rate', 0)
        execution_time = self.metadata.get('execution_time')

        print(f"Task: {{task_name}}")
        print(f"Description: {{description}}")
        print(f"Total Steps: {{total_steps}}")
        print(f"Success Rate: {{success_rate}}%")
        if execution_time:
            print(f"Original Execution Time: {{execution_time}}s")
        print("=" * 60)

    def replay(self, device_id: str = None, delay: float = 1.0):
        """
        Replay the recorded actions.

        Args:
            device_id: Optional device ID
            delay: Delay between actions in seconds
        """
        self.print_info()

        print("\\n🚀 Starting replay...")
        print(f"⚡ Delay between actions: {{delay}}s")
        device_display = device_id or 'default'
        print(f"📱 Device ID: {{device_display}}")

        input("\\nPress Enter to start, or Ctrl+C to cancel...")

        successful_steps = 0

        try:
            for i, step in enumerate(self.steps, 1):
                action_type = step.get('action_type', 'Unknown')
                total_steps_len = len(self.steps)
                print(f"\\n--- Step {{i}}/{{total_steps_len}}: {{action_type}} ---")

                if not step.get('success', True):
                    error_msg = step.get('error_message', 'Unknown error')
                    print(f"⚠️  Skipping failed step: {{error_msg}}")
                    continue

                action_data = step.get('action_data', {{}})
                action_name = action_data.get('action')

                if action_name == 'Launch':
                    app_name = action_data.get('app')
                    if app_name:
                        print(f"🔧 Launching app: {{app_name}}")
                        launch_app(app_name, device_id)

                elif action_name == 'Tap':
                    element = action_data.get('element')
                    if element and len(element) >= 2:
                        x, y = element[0], element[1]
                        print(f"🔧 Tapping at relative coordinates: ({{x}}, {{y}})")
                        # Note: You'll need to implement coordinate conversion for actual tapping
                        # tap(x, y, device_id)

                elif action_name == 'Type':
                    text = action_data.get('text', '')
                    if text:
                        display_text = text[:50] + ('...' if len(text) > 50 else '')
                        print(f"🔧 Typing text: {{display_text}}")
                        # Note: You'll need to implement keyboard switching for actual typing
                        # type_text(text, device_id)

                elif action_name == 'Swipe':
                    start = action_data.get('start')
                    end = action_data.get('end')
                    if start and end and len(start) >= 2 and len(end) >= 2:
                        print(f"🔧 Swiping from {{start}} to {{end}}")
                        # Note: You'll need to implement coordinate conversion for actual swiping
                        # swipe(start_x, start_y, end_x, end_y, device_id)

                elif action_name == 'Back':
                    print("🔧 Pressing back button")
                    back(device_id)

                elif action_name == 'Home':
                    print("🔧 Pressing home button")
                    home(device_id)

                elif action_name == 'Wait':
                    duration = action_data.get('duration', '1 seconds')
                    try:
                        wait_time = float(duration.replace('seconds', '').strip())
                        print(f"🔧 Waiting {{wait_time}}s")
                        time.sleep(wait_time)
                    except ValueError:
                        print(f"🔧 Waiting 1s (default)")
                        time.sleep(1.0)

                else:
                    print(f"⚠️  Unknown action: {{action_name}}")

                successful_steps += 1

                # Wait between actions
                if delay > 0 and i < len(self.steps):
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\\n⚡ Replay interrupted by user")
            return

        print("\\n" + "=" * 60)
        print(f"✅ Replay completed: {{successful_steps}}/{{len(self.steps)}} steps")
        print("=" * 60)


def main():
    """Main function to run the replay script."""
    if len(sys.argv) != 2:
        print("Usage: python {script_name} <script_file.json>")
        sys.exit(1)

    json_file = sys.argv[1]

    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: Script file not found: {{json_file}}")
        sys.exit(1)

    replay = ReplayScript(json_file)

    # Get optional device ID from user
    device_id = input("Enter device ID (press Enter for default): ").strip() or None
    delay_str = input("Enter delay between actions in seconds (default 1.0): ").strip()

    try:
        delay = float(delay_str) if delay_str else 1.0
    except ValueError:
        delay = 1.0
        print("Invalid delay, using default 1.0")

    replay.replay(device_id=device_id, delay=delay)


if __name__ == "__main__":
    main()
'''

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(python_code)

        return str(script_path)

    def get_summary(self) -> str:
        """
        Get a summary of the recorded script.

        Returns:
            Summary string
        """
        if not self.metadata:
            return "No recording in progress"

        summary = f"""
📱 Script Recording Summary:
============================
Task: {self.metadata.task_name}
Steps: {self.metadata.total_steps}
Device: {self.metadata.device_id or 'default'}
Model: {self.metadata.model_name or 'default'}
        """

        if self.steps:
            successful_steps = sum(1 for step in self.steps if step.success)
            success_rate = round(successful_steps / len(self.steps) * 100, 2)
            summary += f"Success Rate: {success_rate}%\n"

            action_counts = {}
            for step in self.steps:
                action_type = step.action_type
                action_counts[action_type] = action_counts.get(action_type, 0) + 1

            summary += "\nAction Breakdown:\n"
            for action, count in sorted(action_counts.items()):
                summary += f"  {action}: {count}\n"

        return summary