#!/usr/bin/env python3
"""
Script Recording Demo - How to use the new script recording functionality
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import phone_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig


def demo_without_recording():
    """Demo without script recording (original behavior)."""
    print("🔹 Demo 1: PhoneAgent without script recording")
    print("=" * 60)

    # Create configurations
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-phone"
    )

    agent_config = AgentConfig(
        max_steps=10,
        device_id=None,  # Auto-detect
        verbose=True,
        record_script=False  # Default behavior
    )

    # Create agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config
    )

    print("✅ Agent created without script recording")
    print(f"📹 Recording enabled: {agent_config.record_script}")
    print()


def demo_with_recording():
    """Demo with script recording enabled."""
    print("🔹 Demo 2: PhoneAgent with script recording enabled")
    print("=" * 60)

    # Create configurations
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-phone"
    )

    agent_config = AgentConfig(
        max_steps=10,
        device_id=None,  # Auto-detect
        verbose=True,
        record_script=True,  # Enable script recording
        script_output_dir="demo_scripts"  # Custom output directory
    )

    # Create agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config
    )

    print("✅ Agent created with script recording")
    print(f"📹 Recording enabled: {agent_config.record_script}")
    print(f"📁 Script output directory: {agent_config.script_output_dir}")
    print(f"📊 Recorder initialized: {agent.recorder is not None}")

    if agent.recorder:
        # Simulate recording some steps
        agent.recorder.start_recording(
            task="Demo task: Open settings and check battery",
            device_id="demo_device",
            model_name="autoglm-phone"
        )

        # Record some mock steps
        mock_actions = [
            {
                "_metadata": "do",
                "action": "Launch",
                "app": "Settings"
            },
            {
                "_metadata": "do",
                "action": "Tap",
                "element": [500, 400]
            },
            {
                "_metadata": "do",
                "action": "Tap",
                "element": [500, 500]
            }
        ]

        thinkings = [
            "Launch Settings app",
            "Tap on Battery option",
            "Check battery level"
        ]

        for action, thinking in zip(mock_actions, thinkings):
            agent.recorder.record_step(
                action=action,
                thinking=thinking,
                success=True
            )

        agent.recorder.finish_recording(success=True)

        # Save the scripts
        json_path = agent.recorder.save_script()
        python_path = agent.recorder.generate_python_script(Path(json_path).name)

        print(f"✅ Scripts saved successfully!")
        print(f"📄 JSON: {json_path}")
        print(f"🐍 Python: {python_path}")

        # Show summary
        print("\n📊 Recording Summary:")
        print(agent.recorder.get_summary())

    print()


def demo_cli_usage():
    """Show CLI usage examples."""
    print("🔹 Demo 3: Command Line Usage Examples")
    print("=" * 60)

    examples = [
        {
            "description": "Run with script recording enabled",
            "command": "python main.py --record-script '打开微信查看未读消息'"
        },
        {
            "description": "Custom script output directory",
            "command": "python main.py --record-script --script-output-dir my_scripts '检查天气应用'"
        },
        {
            "description": "Quiet mode with recording",
            "command": "python main.py --record-script --quiet '发送测试邮件'"
        },
        {
            "description": "With specific device and recording",
            "command": "python main.py --device-id emulator-5554 --record-script '设置闹钟'"
        },
        {
            "description": "Combined with other options",
            "command": "python main.py --record-script --max-steps 50 --lang cn '导航到公司'"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}:")
        print(f"   {example['command']}")
        print()

    print("💡 Notes:")
    print("   - Scripts are saved in JSON format with metadata and steps")
    print("   - Python replay scripts are automatically generated")
    print("   - Screenshots are saved during recording (if available)")
    print("   - Action details, thinking process, and execution results are captured")
    print()


def demo_replay_script():
    """Show how to use generated replay scripts."""
    print("🔹 Demo 4: Using Generated Replay Scripts")
    print("=" * 60)

    print("After running a task with --record-script, you'll get:")
    print("1. A JSON file containing the recorded actions")
    print("2. A Python script that can replay the actions")
    print()

    print("To replay a script:")
    print("1. Run the generated Python script:")
    print("   python scripts/your_task_replay.py scripts/your_task.json")
    print()

    print("2. The replay script will:")
    print("   - Show task information and statistics")
    print("   - Ask for device ID and delay between actions")
    print("   - Replay each action with visual feedback")
    print("   - Handle errors and allow interruption")
    print()

    print("3. Example replay script features:")
    print("   ✅ Launch apps")
    print("   ✅ Tap and swipe gestures")
    print("   ✅ Text input")
    print("   ✅ Navigation actions (back, home)")
    print("   ✅ Wait/delay functionality")
    print("   ✅ Error handling and retry logic")
    print()


def main():
    """Run all demos."""
    print("🚀 Phone Agent Script Recording Demo")
    print("=" * 80)
    print()

    # Demo 1: Without recording
    demo_without_recording()

    # Demo 2: With recording
    demo_with_recording()

    # Demo 3: CLI usage
    demo_cli_usage()

    # Demo 4: Replay usage
    demo_replay_script()

    print("=" * 80)
    print("🎉 Demo completed!")
    print()
    print("Next steps:")
    print("1. Try: python main.py --record-script 'your task here'")
    print("2. Check the 'scripts' directory for generated files")
    print("3. Run the generated replay script to see your actions repeated")
    print("4. Modify replay scripts for custom automation workflows")


if __name__ == "__main__":
    main()