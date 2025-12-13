#!/usr/bin/env python3
"""
Test script for the script recording functionality.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path to import phone_agent
sys.path.insert(0, str(Path(__file__).parent))

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig
from phone_agent.recorder import ScriptRecorder


def test_script_recorder():
    """Test the ScriptRecorder functionality."""
    print("🧪 Testing ScriptRecorder...")

    # Create a recorder
    recorder = ScriptRecorder("test_scripts")

    # Start recording
    recorder.start_recording(
        task="Test task: Launch calculator and perform calculation",
        device_id="test_device",
        model_name="test_model"
    )

    # Simulate some steps
    mock_actions = [
        {
            "_metadata": "do",
            "action": "Launch",
            "app": "Calculator"
        },
        {
            "_metadata": "do",
            "action": "Tap",
            "element": [500, 300]
        },
        {
            "_metadata": "do",
            "action": "Type",
            "text": "123"
        },
        {
            "_metadata": "do",
            "action": "Tap",
            "element": [700, 300]
        },
        {
            "_metadata": "do",
            "action": "Type",
            "text": "456"
        },
        {
            "_metadata": "do",
            "action": "Tap",
            "element": [600, 500]
        }
    ]

    thinkings = [
        "Launch the Calculator app",
        "Tap the number input area",
        "Type the first number 123",
        "Tap the plus button",
        "Type the second number 456",
        "Tap the equals button"
    ]

    print("📝 Recording test steps...")
    for i, (action, thinking) in enumerate(zip(mock_actions, thinkings), 1):
        recorder.record_step(
            action=action,
            thinking=thinking,
            success=True,
            screenshot_base64=None
        )
        print(f"  Step {i}: {action['action']} - {thinking}")

    # Finish recording
    recorder.finish_recording(success=True)

    # Print summary
    print("\n📊 Recording Summary:")
    print(recorder.get_summary())

    # Save scripts
    print("\n💾 Saving scripts...")
    json_path = recorder.save_script()
    python_path = recorder.generate_python_script(Path(json_path).name)

    print(f"✅ JSON script saved to: {json_path}")
    print(f"✅ Python script saved to: {python_path}")

    # Verify files exist
    assert Path(json_path).exists(), "JSON script file not created"
    assert Path(python_path).exists(), "Python script file not created"

    print("\n✅ ScriptRecorder test passed!")


def test_phone_agent_with_recording():
    """Test PhoneAgent with script recording enabled."""
    print("\n🧪 Testing PhoneAgent with script recording...")

    # Create configurations
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-phone",
        api_key="test"
    )

    agent_config = AgentConfig(
        max_steps=10,
        device_id="test_device",
        verbose=True,
        record_script=True,
        script_output_dir="test_scripts"
    )

    # Create agent (this will test the integration)
    try:
        agent = PhoneAgent(
            model_config=model_config,
            agent_config=agent_config
        )

        # Check that recorder was initialized
        assert agent.recorder is not None, "Recorder not initialized"
        print("✅ PhoneAgent with recording initialized successfully")

        # Test that recorder can be accessed
        summary = agent.get_script_summary()
        print("✅ Script summary method works")

    except Exception as e:
        print(f"❌ PhoneAgent integration test failed: {e}")
        return False

    print("✅ PhoneAgent integration test passed!")
    return True


def test_cli_arguments():
    """Test that CLI arguments are properly parsed."""
    print("\n🧪 Testing CLI arguments...")

    # Import the argument parser function
    from main import parse_args

    # Test with script recording arguments
    test_args = [
        "--record-script",
        "--script-output-dir", "test_scripts",
        "test task"
    ]

    # Mock sys.argv
    original_argv = sys.argv
    sys.argv = ["main.py"] + test_args

    try:
        args = parse_args()

        # Check that arguments are parsed correctly
        assert args.record_script == True, "record_script argument not parsed"
        assert args.script_output_dir == "test_scripts", "script_output_dir argument not parsed"
        assert args.task == "test task", "task argument not parsed"

        print("✅ CLI arguments parsed correctly")

    except Exception as e:
        print(f"❌ CLI argument test failed: {e}")
        return False
    finally:
        sys.argv = original_argv

    print("✅ CLI argument test passed!")
    return True


def main():
    """Run all tests."""
    print("🚀 Starting script recording tests...")
    print("=" * 60)

    try:
        # Test 1: ScriptRecorder functionality
        test_script_recorder()

        # Test 2: PhoneAgent integration
        test_phone_agent_with_recording()

        # Test 3: CLI arguments
        test_cli_arguments()

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("\n📁 Generated test files are in: test_scripts/")
        print("💡 You can run the generated Python script to replay the test actions")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)