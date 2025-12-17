"""Main PhoneAgent class for orchestrating phone automation."""

import base64
import json
import logging
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from phone_agent.actions import ActionHandler
from phone_agent.actions.handler import do, finish, parse_action
from phone_agent.adb import get_current_app, get_screenshot
from phone_agent.adb.screenshot import Screenshot
from phone_agent.config import get_messages, get_system_prompt
from phone_agent.model import ModelClient, ModelConfig
from phone_agent.model.client import MessageBuilder
from phone_agent.recorder import ScriptRecorder
from phone_agent.stop_handler import StopSignalHandler, StopException, StopReason

# Import step tracker
try:
    from phone_agent.step_tracker import StepTracker, StepType, StepData
    STEP_TRACKER_AVAILABLE = True
except ImportError:
    STEP_TRACKER_AVAILABLE = False
    StepTracker = None
    StepType = None
    StepData = None

# Configure logger
logger = logging.getLogger(__name__)


def _save_screenshot_to_file(screenshot: Screenshot, save_dir: Path) -> Optional[str]:
    """
    Save screenshot to file and return filename.

    Args:
        screenshot: Screenshot object with base64_data
        save_dir: Directory to save screenshot files

    Returns:
        filename (e.g. 'screenshot_20251213_221530_a1b2c3d4.png') or None if failed
    """
    if not screenshot or not screenshot.base64_data:
        return None

    try:
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_uuid = uuid.uuid4().hex[:8]
        filename = f"screenshot_{timestamp}_{short_uuid}.png"

        # Ensure directory exists
        save_dir.mkdir(parents=True, exist_ok=True)

        # Decode base64 and save
        filepath = save_dir / filename
        image_data = base64.b64decode(screenshot.base64_data)
        filepath.write_bytes(image_data)

        logger.debug(f"Screenshot saved: {filename} ({len(image_data)} bytes)")
        return filename
    except OSError as e:
        if hasattr(e, 'errno'):
            import errno
            if e.errno == errno.ENOSPC:
                logger.error("Disk full, cannot save screenshot")
            elif e.errno == errno.EACCES:
                logger.error("Permission denied, cannot save screenshot")
            else:
                logger.error(f"Failed to save screenshot: {e}")
        else:
            logger.error(f"Failed to save screenshot: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None


@dataclass
class AgentConfig:
    """Configuration for the PhoneAgent."""

    max_steps: int = 100
    device_id: str | None = None
    lang: str = "cn"
    system_prompt: str | None = None
    verbose: bool = True
    record_script: bool = False
    script_output_dir: str = "scripts"

    def __post_init__(self):
        if self.system_prompt is None:
            self.system_prompt = get_system_prompt(self.lang)


@dataclass
class StepResult:
    """Result of a single agent step."""

    success: bool
    finished: bool
    action: dict[str, Any] | None
    thinking: str
    message: str | None = None


class PhoneAgent:
    """
    AI-powered agent for automating Android phone interactions.

    The agent uses a vision-language model to understand screen content
    and decide on actions to complete user tasks.

    Args:
        model_config: Configuration for the AI model.
        agent_config: Configuration for the agent behavior.
        confirmation_callback: Optional callback for sensitive action confirmation.
        takeover_callback: Optional callback for takeover requests.

    Example:
        >>> from phone_agent import PhoneAgent
        >>> from phone_agent.model import ModelConfig
        >>>
        >>> model_config = ModelConfig(base_url="http://localhost:8000/v1")
        >>> agent = PhoneAgent(model_config)
        >>> agent.run("Open WeChat and send a message to John")
    """

    def __init__(
        self,
        model_config: ModelConfig | None = None,
        agent_config: AgentConfig | None = None,
        confirmation_callback: Callable[[str], bool] | None = None,
        takeover_callback: Callable[[str], None] | None = None,
        task_id: str | None = None,
    ):
        self.model_config = model_config or ModelConfig()
        self.agent_config = agent_config or AgentConfig()

        # Store task_id if provided, otherwise will be generated in run()
        self._task_id = task_id

        # Initialize stop signal handler BEFORE other components
        self.stop_handler = StopSignalHandler()
        if self.agent_config.verbose:
            logger.info("✅ Stop signal handler initialized")

        self.model_client = ModelClient(self.model_config, stop_handler=self.stop_handler)
        self.action_handler = ActionHandler(
            device_id=self.agent_config.device_id,
            confirmation_callback=confirmation_callback,
            takeover_callback=takeover_callback,
        )

        self._context: list[dict[str, Any]] = []
        self._step_count = 0

        # Initialize script recorder if enabled
        self.recorder: ScriptRecorder | None = None
        if self.agent_config.record_script:
            self.recorder = ScriptRecorder(self.agent_config.script_output_dir)

        # Initialize step tracker if available
        self.step_tracker: StepTracker | None = None
        # StepTracker will be initialized in run() method after task_id is generated

    def run(self, task: str, step_callback: Callable[[dict], None] = None) -> str:
        """
        Run the agent to complete a task.

        Args:
            task: Natural language description of the task.

        Returns:
            Final message from the agent.
        """
        self._context = []
        self._step_count = 0

        # Generate a task ID for step tracking if not already set
        if not self._task_id:
            self._task_id = str(uuid.uuid4())
            if self.agent_config.verbose:
                print(f"📝 Generated new task_id: {self._task_id}")
        else:
            if self.agent_config.verbose:
                print(f"📝 Using existing task_id: {self._task_id}")

        # Start script recording if enabled
        if self.recorder:
            self.recorder.start_recording(
                task=task,
                device_id=self.agent_config.device_id,
                model_name=self.model_config.model_name
            )

        # Initialize step tracker if available
        if STEP_TRACKER_AVAILABLE:
            try:
                if self.agent_config.verbose:
                    print(f"📊 Initializing step tracker with task_id: {self._task_id}")
                self.step_tracker = StepTracker(self._task_id)
                if self.agent_config.verbose:
                    print(f"✅ Step tracker initialized successfully with task_id: {self._task_id}")
            except Exception as e:
                print(f"⚠️ Failed to initialize step tracker: {e}")
                import traceback
                if self.agent_config.verbose:
                    traceback.print_exc()
                self.step_tracker = None

        try:
            # First step with user prompt
            # Check for stop before first step
            self.check_stop()
            result = self._execute_step(task, is_first=True, step_callback=step_callback)

            if result.finished:
                if self.recorder:
                    self.recorder.finish_recording(result.success)
                    self._save_script()
                return result.message or "Task completed"

            # Continue until finished or max steps reached
            while self._step_count < self.agent_config.max_steps:
                # Check for stop at the beginning of each iteration
                self.check_stop()
                result = self._execute_step(is_first=False, step_callback=step_callback)

                if result.finished:
                    if self.recorder:
                        self.recorder.finish_recording(result.success)
                        self._save_script()
                    return result.message or "Task completed"

            if self.recorder:
                self.recorder.finish_recording(False)
                self._save_script()
            return "Max steps reached"

        except StopException as e:
            # Task was stopped by user
            if self.agent_config.verbose:
                logger.info(f"🛑 Task stopped: {e}")
            if self.recorder:
                self.recorder.finish_recording(False)
                self._save_script()
            return str(e)
        except Exception as e:
            if self.recorder:
                self.recorder.finish_recording(False)
                self._save_script()
            raise e

    def step(self, task: str | None = None) -> StepResult:
        """
        Execute a single step of the agent.

        Useful for manual control or debugging.

        Args:
            task: Task description (only needed for first step).

        Returns:
            StepResult with step details.
        """
        is_first = len(self._context) == 0

        if is_first and not task:
            raise ValueError("Task is required for the first step")

        return self._execute_step(task, is_first)

    def reset(self) -> None:
        """Reset the agent state for a new task."""
        self._context = []
        self._step_count = 0

    def stop(self, reason: StopReason = StopReason.USER_REQUEST, message: str | None = None) -> None:
        """
        停止任务执行

        Args:
            reason: 停止原因
            message: 停止消息
        """
        if self.agent_config.verbose:
            logger.info(f"🛑 Stopping task: {reason.value} - {message or ''}")

        self.stop_handler.stop(reason, message)

        # 停止录制
        if self.recorder:
            self.recorder.stop()

    def should_stop(self) -> bool:
        """
        检查是否应该停止

        Returns:
            bool: 如果应该停止返回True
        """
        return self.stop_handler.should_stop()

    def check_stop(self) -> None:
        """
        检查停止状态，如果需要停止则抛出异常

        Raises:
            StopException: 如果任务应该停止
        """
        self.stop_handler.check_stop()

    def _execute_step(
        self, user_prompt: str | None = None, is_first: bool = False, step_callback: Callable[[dict], None] = None
    ) -> StepResult:
        """Execute a single step of the agent loop."""
        self._step_count += 1

        # Capture current screen state
        screenshot = get_screenshot(self.agent_config.device_id)
        current_app = get_current_app(self.agent_config.device_id)

        # Build messages
        if is_first:
            self._context.append(
                MessageBuilder.create_system_message(self.agent_config.system_prompt)
            )

            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"{user_prompt}\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )
        else:
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"** Screen Info **\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )

        # Get model response
        try:
            # Check for stop before AI call
            self.check_stop()
            response = self.model_client.request(self._context)
            # Check for stop after AI call
            self.check_stop()
        except StopException:
            # Re-raise StopException without wrapping
            raise
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"Model error: {e}",
            )

        # Parse action from response
        try:
            action = parse_action(response.action)
        except ValueError:
            if self.agent_config.verbose:
                traceback.print_exc()
            action = finish(message=response.action)

        if self.agent_config.verbose:
            # Print thinking process
            msgs = get_messages(self.agent_config.lang)
            print("\n" + "=" * 50)
            print(f"💭 {msgs['thinking']}:")
            print("-" * 50)
            print(response.thinking)
            print("-" * 50)
            print(f"🎯 {msgs['action']}:")
            print(json.dumps(action, ensure_ascii=False, indent=2))
            print("=" * 50 + "\n")

        # Remove image from context to save space
        self._context[-1] = MessageBuilder.remove_images_from_message(self._context[-1])

        # Record step before execution
        if self.recorder and action.get("_metadata") != "finish":
            self.recorder.record_step(
                action=action,
                thinking=response.thinking,
                screenshot_base64=screenshot.base64_data
            )

        # Execute action
        try:
            # Check for stop before action execution
            self.check_stop()
            result = self.action_handler.execute(
                action, screenshot.width, screenshot.height
            )
            # Check for stop after action execution
            self.check_stop()
        except StopException:
            # Re-raise StopException without wrapping
            raise
        except Exception as e:
            # Update step recording with execution result
            if self.recorder and action.get("_metadata") != "finish":
                self.recorder.steps[-1].success = result.success
                self.recorder.steps[-1].error_message = result.message if not result.success else None
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            # Update step recording with error
            if self.recorder and action.get("_metadata") != "finish":
                self.recorder.steps[-1].success = False
                self.recorder.steps[-1].error_message = str(e)
            result = self.action_handler.execute(
                finish(message=str(e)), screenshot.width, screenshot.height
            )

        # Add assistant response to context
        self._context.append(
            MessageBuilder.create_assistant_message(
                f"<think>{response.thinking}</think><answer>{response.action}</answer>"
            )
        )

        # Check if finished
        finished = action.get("_metadata") == "finish" or result.should_finish

        if finished and self.agent_config.verbose:
            msgs = get_messages(self.agent_config.lang)
            print("\n" + "🎉 " + "=" * 48)
            print(
                f"✅ {msgs['task_completed']}: {result.message or action.get('message', msgs['done'])}"
            )
            print("=" * 50 + "\n")

        # Call step callback if provided
        if step_callback:
            # Generate unique step ID
            step_id = str(uuid.uuid4())

            # Save screenshot to file
            screenshot_filename = None
            screenshot_path = None
            if screenshot and screenshot.base64_data:
                # Determine screenshots directory (relative to web/static/screenshots)
                # Navigate from phone_agent/ to web/static/screenshots/
                screenshots_dir = Path(__file__).parent.parent / 'web' / 'static' / 'screenshots'
                screenshot_filename = _save_screenshot_to_file(screenshot, screenshots_dir)
                if screenshot_filename:
                    screenshot_path = str(screenshots_dir / screenshot_filename)

            # Record step in StepTracker if available
            if self.step_tracker:
                self.step_tracker.record_step(
                    step_type=StepType.COMPLETION if finished else StepType.ACTION,
                    step_data={
                        'action': action,
                        'result': {
                            'success': result.success,
                            'message': result.message
                        }
                    },
                    thinking=response.thinking,
                    action_result=result,
                    screenshot_path=screenshot_path,
                    success=result.success
                )

            step_data = {
                'step_id': step_id,
                'task_id': getattr(self, '_task_id', ''),
                'step_number': self._step_count,
                'thinking': response.thinking,
                'action': action,
                'result': result,
                'screenshot': screenshot_filename,  # Send filename instead of base64 data
                'screenshot_path': screenshot_path,  # Full path for database
                'success': result.success,
                'finished': finished
            }
            step_callback(step_data)

        return StepResult(
            success=result.success,
            finished=finished,
            action=action,
            thinking=response.thinking,
            message=result.message or action.get("message"),
        )

    @property
    def context(self) -> list[dict[str, Any]]:
        """Get the current conversation context."""
        return self._context.copy()

    def _save_script(self):
        """Save the recorded script if recording is enabled."""
        if not self.recorder or not self.recorder.steps:
            return

        try:
            # Save JSON script
            json_path = self.recorder.save_script()
            # Generate Python replay script
            python_path = self.recorder.generate_python_script(Path(json_path).name)

            if self.agent_config.verbose:
                print("\n" + "📹 " + "=" * 48)
                print("💾 Automation script saved successfully!")
                print(f"📄 JSON script: {json_path}")
                print(f"🐍 Python script: {python_path}")
                print(f"📊 Summary: {len(self.recorder.steps)} steps recorded")

                # Print action breakdown
                action_counts = {}
                for step in self.recorder.steps:
                    action_type = step.action_type
                    action_counts[action_type] = action_counts.get(action_type, 0) + 1

                if action_counts:
                    print("📈 Actions breakdown:")
                    for action, count in sorted(action_counts.items()):
                        print(f"   {action}: {count}")

                print("=" * 50 + "\n")

        except Exception as e:
            if self.agent_config.verbose:
                print(f"❌ Failed to save script: {e}")

    def get_script_summary(self) -> str | None:
        """Get a summary of the recorded script."""
        if self.recorder:
            return self.recorder.get_summary()
        return None

    @property
    def step_count(self) -> int:
        """Get the current step count."""
        return self._step_count
