"""
停止信号处理器

提供线程安全的任务停止机制，支持立即停止和优雅停止。
"""

import threading
import time
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class StopReason(Enum):
    """停止原因枚举"""
    USER_REQUEST = "User requested stop"
    TIMEOUT = "Task timeout"
    ERROR = "Task error"
    SHUTDOWN = "System shutdown"


@dataclass
class StopInfo:
    """停止信息"""
    reason: StopReason
    timestamp: float
    message: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class StopException(Exception):
    """任务停止异常"""

    def __init__(self, message: str, stop_info: Optional[StopInfo] = None):
        super().__init__(message)
        self.stop_info = stop_info or StopInfo(StopReason.USER_REQUEST, time.time())


class StopSignalHandler:
    """
    线程安全的停止信号处理器

    提供快速的跨线程停止信号传递机制。
    """

    def __init__(self):
        """初始化停止信号处理器"""
        self._stop_event = threading.Event()
        self._stop_lock = threading.Lock()
        self._stop_info: Optional[StopInfo] = None
        self._stop_callbacks = []

    def stop(self, reason: StopReason = StopReason.USER_REQUEST, message: Optional[str] = None) -> None:
        """
        设置停止信号

        Args:
            reason: 停止原因
            message: 停止消息
        """
        with self._stop_lock:
            if not self._stop_event.is_set():
                self._stop_info = StopInfo(reason, time.time(), message)
                self._stop_event.set()

                # 调用停止回调
                for callback in self._stop_callbacks:
                    try:
                        callback(self._stop_info)
                    except Exception as e:
                        # 不让回调错误影响主流程
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error in stop callback: {e}")

    def should_stop(self) -> bool:
        """
        检查是否应该停止

        Returns:
            bool: 如果应该停止返回True
        """
        return self._stop_event.is_set()

    def check_stop(self) -> None:
        """
        检查停止状态，如果需要停止则抛出异常

        Raises:
            StopException: 如果任务应该停止
        """
        if self.should_stop():
            raise StopException(self.get_stop_message(), self._stop_info)

    def get_stop_info(self) -> Optional[StopInfo]:
        """
        获取停止信息

        Returns:
            StopInfo: 停止信息，如果没有停止信号则返回None
        """
        with self._stop_lock:
            return self._stop_info

    def get_stop_message(self) -> str:
        """
        获取停止消息

        Returns:
            str: 停止消息
        """
        with self._stop_lock:
            if self._stop_info:
                if self._stop_info.message:
                    return self._stop_info.message
                return self._stop_info.reason.value
            return "Task stopped"

    def reset(self) -> None:
        """重置停止信号"""
        with self._stop_lock:
            self._stop_event.clear()
            self._stop_info = None

    def wait_for_stop(self, timeout: Optional[float] = None) -> bool:
        """
        等待停止信号

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 如果收到停止信号返回True，超时返回False
        """
        return self._stop_event.wait(timeout)

    def add_stop_callback(self, callback) -> None:
        """
        添加停止回调函数

        Args:
            callback: 回调函数，接收StopInfo参数
        """
        with self._stop_lock:
            self._stop_callbacks.append(callback)

    def remove_stop_callback(self, callback) -> None:
        """
        移除停止回调函数

        Args:
            callback: 要移除的回调函数
        """
        with self._stop_lock:
            if callback in self._stop_callbacks:
                self._stop_callbacks.remove(callback)


class StoppableMixin:
    """
    可停止功能的混入类

    为其他类提供停止功能的通用接口。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_handler = StopSignalHandler()

    def stop(self, reason: StopReason = StopReason.USER_REQUEST, message: Optional[str] = None) -> None:
        """
        停止执行

        Args:
            reason: 停止原因
            message: 停止消息
        """
        self._stop_handler.stop(reason, message)

    def should_stop(self) -> bool:
        """
        检查是否应该停止

        Returns:
            bool: 如果应该停止返回True
        """
        return self._stop_handler.should_stop()

    def check_stop(self) -> None:
        """
        检查停止状态，如果需要停止则抛出异常

        Raises:
            StopException: 如果任务应该停止
        """
        self._stop_handler.check_stop()

    def get_stop_info(self) -> Optional[StopInfo]:
        """
        获取停止信息

        Returns:
            StopInfo: 停止信息
        """
        return self._stop_handler.get_stop_info()

    def reset_stop_signal(self) -> None:
        """重置停止信号"""
        self._stop_handler.reset()


# 便利函数
def create_stop_handler() -> StopSignalHandler:
    """
    创建停止信号处理器

    Returns:
        StopSignalHandler: 新的停止信号处理器实例
    """
    return StopSignalHandler()


def check_stop_signal(handler: StopSignalHandler) -> None:
    """
    检查停止信号的便利函数

    Args:
        handler: 停止信号处理器

    Raises:
        StopException: 如果应该停止
    """
    handler.check_stop()