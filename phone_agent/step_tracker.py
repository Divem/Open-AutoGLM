"""
Step tracking system for Open-AutoGLM
Captures detailed execution steps during task execution
"""

import os
import json
import uuid
import time
import hashlib
import threading
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
import pickle

# Import screenshot manager for Supabase integration
try:
    from web.screenshot_manager import get_screenshot_manager
    SCREENSHOT_MANAGER_AVAILABLE = True
except ImportError:
    SCREENSHOT_MANAGER_AVAILABLE = False
    print("Warning: Screenshot manager not available, Supabase upload disabled")

# Import Supabase manager for database integration
try:
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    from web.supabase_manager import SupabaseTaskManager
    SUPABASE_MANAGER_AVAILABLE = True
except ImportError:
    SUPABASE_MANAGER_AVAILABLE = False
    print("Warning: Supabase manager not available, database integration disabled")

# Configure logging
logger = logging.getLogger(__name__)

class StepType(Enum):
    """Step execution types"""
    THINKING = "thinking"
    ACTION = "action"
    SCREENSHOT = "screenshot"
    ERROR = "error"
    VALIDATION = "validation"
    COMPLETION = "completion"

@dataclass
class StepData:
    """Data structure for a single execution step"""
    step_id: str
    task_id: str
    step_number: int
    step_type: StepType
    step_data: Dict[str, Any]
    thinking: Optional[str] = None
    action_result: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert StepType enum to string
        if isinstance(data.get('step_type'), StepType):
            data['step_type'] = data['step_type'].value
        # Convert datetime to ISO string
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepData':
        """Create from dictionary"""
        # Convert step_type string to enum
        if isinstance(data.get('step_type'), str):
            try:
                data['step_type'] = StepType(data['step_type'])
            except ValueError:
                data['step_type'] = StepType.ACTION  # Default

        # Convert ISO string to datetime
        if isinstance(data.get('timestamp'), str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                data['timestamp'] = datetime.now()

        return cls(**data)

@dataclass
class ScreenshotInfo:
    """Information about a screenshot file"""
    local_path: str
    file_size: int
    file_hash: str
    compressed: bool = False
    metadata: Optional[Dict[str, Any]] = None
    remote_url: Optional[str] = None  # For future Supabase integration

class StepTracker:
    """Tracks and manages execution steps during task execution"""

    def __init__(self, task_id: str, buffer_size: int = 50, flush_interval: float = 5.0, enable_database: bool = True):
        self.task_id = task_id
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # Step tracking
        self.steps: List[StepData] = []
        self.current_step_number = 0
        self.step_start_time: Optional[float] = None

        # Buffer and async writing
        self.buffer: Queue[StepData] = Queue(maxsize=buffer_size * 2)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="StepTracker")
        self.flush_timer: Optional[threading.Timer] = None

        # State
        self.is_enabled = True
        self.is_flushing = False
        self.total_steps = 0
        self.successful_steps = 0
        self.failed_steps = 0
        self.total_duration_ms = 0

        # Screenshots
        self.screenshots: Dict[str, ScreenshotInfo] = {}

        # Callbacks
        self.step_callbacks: List[Callable[[StepData], None]] = []

        # Database integration
        self.enable_database = enable_database and SUPABASE_MANAGER_AVAILABLE
        self.db_manager = None

        if self.enable_database:
            try:
                self.db_manager = SupabaseTaskManager()
                logger.info("✅ StepTracker database integration enabled")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize database manager: {e}")
                self.enable_database = False
        else:
            logger.info("ℹ️ StepTracker database integration disabled")

        # Start flush timer
        self._start_flush_timer()

        logger.info(f"StepTracker initialized for task: {task_id}")

    def enable(self):
        """Enable step tracking"""
        self.is_enabled = True
        logger.info(f"Step tracking enabled for task: {self.task_id}")

    def disable(self):
        """Disable step tracking"""
        self.is_enabled = False
        logger.info(f"Step tracking disabled for task: {self.task_id}")

    def add_step_callback(self, callback: Callable[[StepData], None]):
        """Add a callback to be called when a step is recorded"""
        self.step_callbacks.append(callback)

    def start_step(self, step_type: StepType, step_data: Dict[str, Any]) -> str:
        """Start tracking a new step"""
        if not self.is_enabled:
            return ""

        self.current_step_number += 1
        self.total_steps += 1
        self.step_start_time = time.time()

        step_id = str(uuid.uuid4())
        step = StepData(
            step_id=step_id,
            task_id=self.task_id,
            step_number=self.current_step_number,
            step_type=step_type,
            step_data=step_data,
            timestamp=datetime.now()
        )

        return step_id

    def finish_step(self,
                   step_id: str,
                   thinking: Optional[str] = None,
                   action_result: Optional[Dict[str, Any]] = None,
                   screenshot_path: Optional[str] = None,
                   success: bool = True,
                   error_message: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """Finish tracking a step"""
        if not self.is_enabled or not step_id:
            return

        # Calculate duration
        duration_ms = None
        if self.step_start_time:
            duration_ms = int((time.time() - self.step_start_time) * 1000)
            self.total_duration_ms += duration_ms

        # Update statistics
        if success:
            self.successful_steps += 1
        else:
            self.failed_steps += 1

        # Create step data
        step = StepData(
            step_id=step_id,
            task_id=self.task_id,
            step_number=self.current_step_number,
            step_type=StepType.ACTION,  # Default for finish_step
            step_data={},
            thinking=thinking,
            action_result=action_result,
            screenshot_path=screenshot_path,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(),
            metadata=metadata
        )

        # Record screenshot if provided
        if screenshot_path and os.path.exists(screenshot_path):
            self._record_screenshot(screenshot_path)

        # Add to buffer
        self._add_to_buffer(step)

        # Call callbacks
        for callback in self.step_callbacks:
            try:
                callback(step)
            except Exception as e:
                logger.error(f"Step callback error: {e}")

    def record_step(self,
                   step_type: StepType,
                   step_data: Dict[str, Any],
                   thinking: Optional[str] = None,
                   action_result: Optional[Dict[str, Any]] = None,
                   screenshot_path: Optional[str] = None,
                   success: bool = True,
                   error_message: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """Record a complete step in one call"""
        if not self.is_enabled:
            return

        self.current_step_number += 1
        self.total_steps += 1

        step_id = str(uuid.uuid4())
        step = StepData(
            step_id=step_id,
            task_id=self.task_id,
            step_number=self.current_step_number,
            step_type=step_type,
            step_data=step_data,
            thinking=thinking,
            action_result=action_result,
            screenshot_path=screenshot_path,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(),
            metadata=metadata
        )

        # Record screenshot if provided
        if screenshot_path and os.path.exists(screenshot_path):
            self._record_screenshot(screenshot_path)

        # Update statistics
        if success:
            self.successful_steps += 1
        else:
            self.failed_steps += 1

        # Add to buffer
        self._add_to_buffer(step)

        # Call callbacks
        for callback in self.step_callbacks:
            try:
                callback(step)
            except Exception as e:
                logger.error(f"Step callback error: {e}")

    def _record_screenshot(self, screenshot_path: str, task_id: Optional[str] = None, step_id: Optional[str] = None):
        """Record screenshot information and trigger upload"""
        try:
            if not os.path.exists(screenshot_path):
                logger.warning(f"Screenshot file not found: {screenshot_path}")
                return

            # Get file info
            stat = os.stat(screenshot_path)
            file_size = stat.st_size

            # Calculate file hash
            file_hash = self._calculate_file_hash(screenshot_path)

            # Store screenshot info
            self.screenshots[screenshot_path] = ScreenshotInfo(
                local_path=screenshot_path,
                file_size=file_size,
                file_hash=file_hash,
                compressed=False,
                metadata={
                    "captured_at": datetime.now().isoformat(),
                    "task_id": task_id,
                    "step_id": step_id
                }
            )

            # Trigger Supabase upload if available
            if SCREENSHOT_MANAGER_AVAILABLE and task_id:
                screenshot_manager = get_screenshot_manager()
                if screenshot_manager:
                    try:
                        # Run upload in background
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        # Queue for async upload
                        upload_id = loop.run_until_complete(
                            screenshot_manager.queue_upload(screenshot_path, task_id, step_id)
                        )

                        logger.info(f"Screenshot queued for upload: {upload_id}")

                        # Store upload ID in metadata
                        self.screenshots[screenshot_path].metadata["upload_id"] = upload_id

                    except Exception as upload_error:
                        logger.error(f"Failed to queue screenshot for upload: {upload_error}")

        except Exception as e:
            logger.error(f"Failed to record screenshot: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {e}")
            return ""

    def _add_to_buffer(self, step: StepData):
        """Add step to buffer for async writing"""
        try:
            # Add to in-memory list
            self.steps.append(step)

            # Add to buffer queue
            self.buffer.put(step, block=False)

            # Check if buffer is full
            if self.buffer.qsize() >= self.buffer_size:
                logger.info("Buffer full, triggering flush")
                self.executor.submit(self._flush_buffer)

        except Exception as e:
            logger.error(f"Failed to add step to buffer: {e}")

    def _start_flush_timer(self):
        """Start periodic flush timer"""
        if self.flush_timer:
            self.flush_timer.cancel()

        self.flush_timer = threading.Timer(self.flush_interval, self._periodic_flush)
        self.flush_timer.daemon = True
        self.flush_timer.start()

    def _periodic_flush(self):
        """Periodic flush callback"""
        if not self.buffer.empty():
            self.executor.submit(self._flush_buffer)

        # Restart timer
        self._start_flush_timer()

    def _flush_buffer(self):
        """Flush buffer to persistent storage"""
        if self.is_flushing:
            return

        self.is_flushing = True
        steps_to_flush = []

        try:
            # Collect steps from buffer
            while not self.buffer.empty():
                try:
                    step = self.buffer.get_nowait()
                    steps_to_flush.append(step)
                except Empty:
                    break

            if steps_to_flush:
                # Save to database if available
                if self.enable_database:
                    self._save_to_database(steps_to_flush)

                # Save to local file as backup
                self._save_to_local_file(steps_to_flush)
                logger.info(f"Flushed {len(steps_to_flush)} steps")

        except Exception as e:
            logger.error(f"Failed to flush buffer: {e}")
        finally:
            self.is_flushing = False

    def _save_to_database(self, steps: List[StepData]):
        """Save steps to Supabase database"""
        if not self.db_manager or not steps:
            return

        try:
            logger.info(f"💾 Attempting to save {len(steps)} steps to database")
            saved_count = 0
            screenshot_count = 0

            for step in steps:
                try:
                    # Prepare step record for database
                    step_record = {
                        'task_id': self.task_id,
                        'step_number': step.step_number,
                        'step_type': step.step_type.value if isinstance(step.step_type, StepType) else str(step.step_type),
                        'step_data': step.step_data,
                        'thinking': step.thinking,
                        'action_result': step.action_result,
                        'screenshot_path': step.screenshot_path,
                        'duration_ms': step.duration_ms,
                        'success': step.success,
                        'error_message': step.error_message,
                        'created_at': datetime.now().isoformat()
                    }

                    # Save step to task_steps table
                    saved_step_id = self.db_manager.save_step(step_record)

                    if saved_step_id:
                        saved_count += 1

                        # Save screenshot information to step_screenshots table
                        if step.screenshot_path:
                            try:
                                screenshot_info = self.screenshots.get(step.screenshot_path)
                                if screenshot_info:
                                    screenshot_record = {
                                        'id': str(uuid.uuid4()),
                                        'task_id': self.task_id,
                                        'step_id': saved_step_id,
                                        'screenshot_path': step.screenshot_path,
                                        'file_size': screenshot_info.file_size,
                                        'file_hash': screenshot_info.file_hash,
                                        'compressed': screenshot_info.compressed,
                                        'metadata': {
                                            'step_number': step.step_number,
                                            'step_type': step.step_type.value if isinstance(step.step_type, StepType) else str(step.step_type)
                                        },
                                        'created_at': datetime.now().isoformat()
                                    }

                                    saved_screenshot_id = self.db_manager.save_step_screenshot(screenshot_record)
                                    if saved_screenshot_id:
                                        screenshot_count += 1
                                        logger.debug(f"✅ Saved screenshot: {step.screenshot_path}")
                                    else:
                                        logger.warning(f"⚠️ Failed to save screenshot: {step.screenshot_path}")
                                else:
                                    # No screenshot info available, create basic record
                                    screenshot_record = {
                                        'id': str(uuid.uuid4()),
                                        'task_id': self.task_id,
                                        'step_id': saved_step_id,
                                        'screenshot_path': step.screenshot_path,
                                        'file_size': None,
                                        'file_hash': None,
                                        'compressed': False,
                                        'metadata': None,
                                        'created_at': datetime.now().isoformat()
                                    }

                                    saved_screenshot_id = self.db_manager.save_step_screenshot(screenshot_record)
                                    if saved_screenshot_id:
                                        screenshot_count += 1

                            except Exception as screenshot_error:
                                logger.error(f"Failed to save screenshot {step.screenshot_path}: {screenshot_error}")
                    else:
                        logger.error(f"❌ Failed to save step {step.step_number} - no ID returned")

                except Exception as step_error:
                    logger.error(f"Failed to save step {step.step_number}: {step_error}")

            logger.info(f"✅ Saved {saved_count} steps and {screenshot_count} screenshots to database")

        except Exception as e:
            logger.error(f"Failed to save steps to database: {e}")
            logger.exception("Full traceback:")

    def _save_to_local_file(self, steps: List[StepData]):
        """Save steps to local file as backup"""
        try:
            # Create backup directory
            backup_dir = Path("backup/steps")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{self.task_id}_{timestamp}.pkl"

            with open(backup_file, 'wb') as f:
                pickle.dump([step.to_dict() for step in steps], f)

            logger.debug(f"Saved steps to backup file: {backup_file}")

        except Exception as e:
            logger.error(f"Failed to save steps to local file: {e}")

    def flush(self):
        """Manually flush all buffered steps"""
        self.executor.submit(self._flush_buffer)
        self.executor.shutdown(wait=True)

    def get_statistics(self) -> Dict[str, Any]:
        """Get step tracking statistics"""
        return {
            "task_id": self.task_id,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "success_rate": self.successful_steps / max(self.total_steps, 1),
            "total_duration_ms": self.total_duration_ms,
            "average_step_duration_ms": self.total_duration_ms / max(self.total_steps, 1),
            "screenshots_count": len(self.screenshots),
            "is_enabled": self.is_enabled,
            "buffer_size": self.buffer.qsize()
        }

    def get_steps(self, limit: Optional[int] = None) -> List[StepData]:
        """Get recorded steps"""
        if limit:
            return self.steps[-limit:]
        return self.steps.copy()

    def cleanup(self):
        """Clean up resources"""
        self.flush()

        if self.flush_timer:
            self.flush_timer.cancel()

        self.executor.shutdown(wait=True)
        logger.info(f"StepTracker cleaned up for task: {self.task_id}")