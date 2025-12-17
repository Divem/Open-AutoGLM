"""Model client for AI inference using OpenAI-compatible API."""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from openai import OpenAI


class TimeoutMonitor:
    """Simple timeout monitoring and statistics."""

    def __init__(self):
        self.request_stats = []
        self.max_stats = 1000  # Keep only last 1000 requests

    def record_request(self, model_name: str, duration: float, success: bool, timeout: float):
        """Record request statistics."""
        stat = {
            'timestamp': time.time(),
            'model': model_name,
            'duration': duration,
            'success': success,
            'timeout': timeout,
            'is_timeout': not success and duration >= timeout,
        }
        self.request_stats.append(stat)

        # Keep only recent stats
        if len(self.request_stats) > self.max_stats:
            self.request_stats = self.request_stats[-self.max_stats:]

    def get_timeout_rate(self, hours: int = 24) -> float:
        """Get timeout rate in the last N hours."""
        cutoff_time = time.time() - hours * 3600
        recent_requests = [r for r in self.request_stats if r['timestamp'] > cutoff_time]

        if not recent_requests:
            return 0.0

        timeout_count = sum(1 for r in recent_requests if r['is_timeout'])
        return timeout_count / len(recent_requests)

    def get_average_duration(self, model_name: str = None, hours: int = 24) -> float:
        """Get average request duration."""
        cutoff_time = time.time() - hours * 3600
        recent_requests = [r for r in self.request_stats
                          if r['timestamp'] > cutoff_time and r['success']
                          and (model_name is None or r['model'] == model_name)]

        if not recent_requests:
            return 0.0

        return sum(r['duration'] for r in recent_requests) / len(recent_requests)

    def get_stats_summary(self, hours: int = 24) -> dict:
        """Get comprehensive statistics summary."""
        cutoff_time = time.time() - hours * 3600
        recent_requests = [r for r in self.request_stats if r['timestamp'] > cutoff_time]

        if not recent_requests:
            return {}

        total_requests = len(recent_requests)
        successful_requests = sum(1 for r in recent_requests if r['success'])
        timeout_requests = sum(1 for r in recent_requests if r['is_timeout'])

        return {
            'total_requests': total_requests,
            'success_rate': successful_requests / total_requests,
            'timeout_rate': timeout_requests / total_requests,
            'average_duration': sum(r['duration'] for r in recent_requests) / total_requests,
            'models': list(set(r['model'] for r in recent_requests)),
        }


class TimeoutStrategy:
    """Dynamic timeout calculation strategy based on request complexity."""

    def __init__(self, config: TimeoutConfig = None):
        self.config = config or TimeoutConfig()

    def calculate_timeout(self, messages: list[dict[str, Any]]) -> float:
        """Calculate optimal timeout based on message content."""
        if not self.config.enable_adaptive:
            return self.config.base_timeout

        content_size = 0
        image_count = 0

        for msg in messages:
            if isinstance(msg.get('content'), str):
                content_size += len(msg['content'])
            elif isinstance(msg.get('content'), list):
                for item in msg['content']:
                    if item.get('type') == 'text':
                        content_size += len(item.get('text', ''))
                    elif item.get('type') == 'image_url':
                        image_count += 1

        # Calculate timeout: base + content complexity + image processing
        timeout = self.config.base_timeout
        timeout += content_size * self.config.content_factor
        timeout += image_count * self.config.image_factor

        return min(timeout, self.config.max_timeout)

    def get_model_timeout(self, model_name: str) -> float:
        """Get model-specific default timeout."""
        return self.config.get_model_timeout(model_name)


class RetryManager:
    """Enhanced retry manager for AI model requests."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_delays = [1, 2, 4]  # Retry delays in seconds

    def execute_with_retry(self, func, stop_handler=None, *args, **kwargs):
        """Execute a function with retry logic and stop signal awareness."""
        last_exception = None
        original_timeout = kwargs.get('timeout', 30.0)

        for attempt in range(self.max_retries + 1):
            try:
                # Adjust timeout for retry attempts
                if attempt > 0:
                    adjusted_timeout = min(original_timeout * (1.5 ** attempt), 120.0)  # Max 120 seconds
                    kwargs['timeout'] = adjusted_timeout

                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # Check if this is a timeout error
                is_timeout = "timeout" in error_msg or "timed out" in error_msg

                if is_timeout and attempt < self.max_retries:
                    # Check for stop signal before retry
                    if stop_handler and stop_handler.should_stop():
                        from phone_agent.stop_handler import StopException
                        raise StopException(f"Task stopped during retry attempt {attempt + 1}")

                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    time.sleep(delay)
                    continue
                elif is_timeout:
                    raise TimeoutError(f"Request timed out after {self.max_retries + 1} attempts")
                else:
                    # Non-timeout errors should be raised immediately
                    raise e

        raise last_exception


@dataclass
class TimeoutConfig:
    """Configuration for timeout management."""

    base_timeout: float = 25.0
    max_timeout: float = 90.0
    max_retries: int = 3
    enable_adaptive: bool = True
    content_factor: float = 0.001
    image_factor: float = 8.0

    # Model-specific timeouts
    model_timeouts: dict[str, float] = field(default_factory=lambda: {
        'autoglm-phone-9b': 35.0,
        'gpt-4-vision-preview': 30.0,
        'claude-3': 25.0,
        'gpt-3.5-turbo': 20.0,
    })

    def get_model_timeout(self, model_name: str) -> float:
        """Get model-specific timeout."""
        return self.model_timeouts.get(model_name, self.base_timeout)


@dataclass
class ModelConfig:
    """Configuration for the AI model."""

    base_url: str = "http://localhost:8000/v1"
    api_key: str = "EMPTY"
    model_name: str = "autoglm-phone-9b"
    max_tokens: int = 3000
    temperature: float = 0.0
    top_p: float = 0.85
    frequency_penalty: float = 0.2
    extra_body: dict[str, Any] = field(default_factory=dict)
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)


@dataclass
class ModelResponse:
    """Response from the AI model."""

    thinking: str
    action: str
    raw_content: str


class ModelClient:
    """
    Client for interacting with OpenAI-compatible vision-language models.

    Args:
        config: Model configuration.
        stop_handler: Optional stop signal handler for interruption support.
    """

    def __init__(self, config: ModelConfig | None = None, stop_handler=None):
        self.config = config or ModelConfig()
        self.client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)
        self.stop_handler = stop_handler
        self.retry_manager = RetryManager(max_retries=self.config.timeout_config.max_retries)
        self.timeout_strategy = TimeoutStrategy(self.config.timeout_config)
        self.monitor = TimeoutMonitor()  # Global monitor instance

    def request(self, messages: list[dict[str, Any]], timeout: float = None) -> ModelResponse:
        """
        Send a request to the model with adaptive timeout and enhanced retry logic.

        Args:
            messages: List of message dictionaries in OpenAI format.
            timeout: Optional explicit timeout. If None, uses adaptive calculation.

        Returns:
            ModelResponse containing thinking and action.

        Raises:
            ValueError: If the response cannot be parsed.
            TimeoutError: If the request times out after all retries.
        """
        # Calculate timeout if not provided
        if timeout is None:
            timeout = self.timeout_strategy.calculate_timeout(messages)

        def make_request(timeout):
            # Check for stop before making request
            if self.stop_handler and self.stop_handler.should_stop():
                from phone_agent.stop_handler import StopException
                raise StopException("Task stopped before AI call")

            response = self.client.chat.completions.create(
                messages=messages,
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                extra_body=self.config.extra_body,
                stream=False,
                timeout=timeout,
            )

            # Check for stop after getting response
            if self.stop_handler and self.stop_handler.should_stop():
                from phone_agent.stop_handler import StopException
                raise StopException("Task stopped after AI call")

            raw_content = response.choices[0].message.content

            # Parse thinking and action from response
            thinking, action = self._parse_response(raw_content)

            return ModelResponse(thinking=thinking, action=action, raw_content=raw_content)

        # Monitor request performance
        start_time = time.time()
        success = False

        try:
            result = self.retry_manager.execute_with_retry(
                make_request,
                self.stop_handler,
                timeout
            )
            success = True
            return result

        except Exception as e:
            # Re-raise StopException without modification
            if "stopped" in str(e):
                raise
            try:
                from phone_agent.stop_handler import StopException
                if isinstance(e, StopException):
                    raise
            except ImportError:
                pass
            raise

        finally:
            # Record request statistics
            duration = time.time() - start_time
            self.monitor.record_request(
                model_name=self.config.model_name,
                duration=duration,
                success=success,
                timeout=timeout
            )

    def get_performance_stats(self, hours: int = 24) -> dict:
        """Get performance statistics for monitoring."""
        return self.monitor.get_stats_summary(hours)

    def _parse_response(self, content: str) -> tuple[str, str]:
        """
        Parse the model response into thinking and action parts.

        Parsing rules:
        1. If content contains 'finish(message=', everything before is thinking,
           everything from 'finish(message=' onwards is action.
        2. If rule 1 doesn't apply but content contains 'do(action=',
           everything before is thinking, everything from 'do(action=' onwards is action.
        3. Fallback: If content contains '<answer>', use legacy parsing with XML tags.
        4. Otherwise, return empty thinking and full content as action.

        Args:
            content: Raw response content.

        Returns:
            Tuple of (thinking, action).
        """
        # Rule 1: Check for finish(message=
        if "finish(message=" in content:
            parts = content.split("finish(message=", 1)
            thinking = parts[0].strip()
            action = "finish(message=" + parts[1]
            return thinking, action

        # Rule 2: Check for do(action=
        if "do(action=" in content:
            parts = content.split("do(action=", 1)
            thinking = parts[0].strip()
            action = "do(action=" + parts[1]
            return thinking, action

        # Rule 3: Fallback to legacy XML tag parsing
        if "<answer>" in content:
            parts = content.split("<answer>", 1)
            thinking = parts[0].replace("<think>", "").replace("</think>", "").strip()
            action = parts[1].replace("</answer>", "").strip()
            return thinking, action

        # Rule 4: No markers found, return content as action
        return "", content


class MessageBuilder:
    """Helper class for building conversation messages."""

    @staticmethod
    def create_system_message(content: str) -> dict[str, Any]:
        """Create a system message."""
        return {"role": "system", "content": content}

    @staticmethod
    def create_user_message(
        text: str, image_base64: str | None = None
    ) -> dict[str, Any]:
        """
        Create a user message with optional image.

        Args:
            text: Text content.
            image_base64: Optional base64-encoded image.

        Returns:
            Message dictionary.
        """
        content = []

        if image_base64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                }
            )

        content.append({"type": "text", "text": text})

        return {"role": "user", "content": content}

    @staticmethod
    def create_assistant_message(content: str) -> dict[str, Any]:
        """Create an assistant message."""
        return {"role": "assistant", "content": content}

    @staticmethod
    def remove_images_from_message(message: dict[str, Any]) -> dict[str, Any]:
        """
        Remove image content from a message to save context space.

        Args:
            message: Message dictionary.

        Returns:
            Message with images removed.
        """
        if isinstance(message.get("content"), list):
            message["content"] = [
                item for item in message["content"] if item.get("type") == "text"
            ]
        return message

    @staticmethod
    def build_screen_info(current_app: str, **extra_info) -> str:
        """
        Build screen info string for the model.

        Args:
            current_app: Current app name.
            **extra_info: Additional info to include.

        Returns:
            JSON string with screen info.
        """
        info = {"current_app": current_app, **extra_info}
        return json.dumps(info, ensure_ascii=False)
