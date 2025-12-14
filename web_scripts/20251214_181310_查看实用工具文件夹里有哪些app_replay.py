#!/usr/bin/env python3
"""
Auto-generated replay script for Phone Agent task.
Generated on: 2025-12-14T18:13:10.195863

To run this script:
    python 20251214_181310_查看实用工具文件夹里有哪些app_replay.py

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
        self.metadata = self.script_data.get("metadata", {})
        self.steps = self.script_data.get("steps", [])

    def _load_script(self) -> dict:
        """Load the script data from JSON file."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Script file not found: {self.json_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in script file: {e}")
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

        print(f"Task: {task_name}")
        print(f"Description: {description}")
        print(f"Total Steps: {total_steps}")
        print(f"Success Rate: {success_rate}%")
        if execution_time:
            print(f"Original Execution Time: {execution_time}s")
        print("=" * 60)

    def replay(self, device_id: str = None, delay: float = 1.0):
        """
        Replay the recorded actions.

        Args:
            device_id: Optional device ID
            delay: Delay between actions in seconds
        """
        self.print_info()

        print("\n🚀 Starting replay...")
        print(f"⚡ Delay between actions: {delay}s")
        device_display = device_id or 'default'
        print(f"📱 Device ID: {device_display}")

        input("\nPress Enter to start, or Ctrl+C to cancel...")

        successful_steps = 0

        try:
            for i, step in enumerate(self.steps, 1):
                action_type = step.get('action_type', 'Unknown')
                total_steps_len = len(self.steps)
                print(f"\n--- Step {i}/{total_steps_len}: {action_type} ---")

                if not step.get('success', True):
                    error_msg = step.get('error_message', 'Unknown error')
                    print(f"⚠️  Skipping failed step: {error_msg}")
                    continue

                action_data = step.get('action_data', {})
                action_name = action_data.get('action')

                if action_name == 'Launch':
                    app_name = action_data.get('app')
                    if app_name:
                        print(f"🔧 Launching app: {app_name}")
                        launch_app(app_name, device_id)

                elif action_name == 'Tap':
                    element = action_data.get('element')
                    if element and len(element) >= 2:
                        x, y = element[0], element[1]
                        print(f"🔧 Tapping at relative coordinates: ({x}, {y})")
                        # Note: You'll need to implement coordinate conversion for actual tapping
                        # tap(x, y, device_id)

                elif action_name == 'Type':
                    text = action_data.get('text', '')
                    if text:
                        display_text = text[:50] + ('...' if len(text) > 50 else '')
                        print(f"🔧 Typing text: {display_text}")
                        # Note: You'll need to implement keyboard switching for actual typing
                        # type_text(text, device_id)

                elif action_name == 'Swipe':
                    start = action_data.get('start')
                    end = action_data.get('end')
                    if start and end and len(start) >= 2 and len(end) >= 2:
                        print(f"🔧 Swiping from {start} to {end}")
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
                        print(f"🔧 Waiting {wait_time}s")
                        time.sleep(wait_time)
                    except ValueError:
                        print(f"🔧 Waiting 1s (default)")
                        time.sleep(1.0)

                else:
                    print(f"⚠️  Unknown action: {action_name}")

                successful_steps += 1

                # Wait between actions
                if delay > 0 and i < len(self.steps):
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\n⚡ Replay interrupted by user")
            return

        print("\n" + "=" * 60)
        print(f"✅ Replay completed: {successful_steps}/{len(self.steps)} steps")
        print("=" * 60)


def main():
    """Main function to run the replay script."""
    if len(sys.argv) != 2:
        print("Usage: python 20251214_181310_查看实用工具文件夹里有哪些app_replay.py <script_file.json>")
        sys.exit(1)

    json_file = sys.argv[1]

    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: Script file not found: {json_file}")
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
