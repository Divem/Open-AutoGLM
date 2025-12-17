#!/usr/bin/env python3
"""
Supabase 任务管理器
用于替换本地pickle文件存储，使用Supabase云数据库进行任务持久化
"""

import os
import json
import threading
import uuid
import logging
import dataclasses
import re
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from functools import lru_cache
from supabase import create_client, Client

# 配置日志
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 从环境变量获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SECRET_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# 时区安全处理函数
def normalize_datetime(dt: datetime) -> datetime:
    """
    将datetime转换为无时区时间以避免时区比较错误

    Args:
        dt: datetime对象，可能有或无时区信息

    Returns:
        datetime: 无时区的datetime对象
    """
    if dt is None:
        return dt

    if dt.tzinfo is not None:
        # 有时区时间 -> 转换为UTC并移除时区信息
        try:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except (AttributeError, ValueError) as e:
            logger.warning(f"时区转换失败，使用原始时间: {e}")
            return dt
    else:
        # 已经是无时区时间 -> 直接返回
        return dt

def safe_datetime_sort_key(task) -> datetime:
    """
    安全的排序键函数，处理时区问题

    Args:
        task: GlobalTask对象

    Returns:
        datetime: 可用于排序的datetime对象
    """
    if hasattr(task, 'created_at') and task.created_at is not None:
        return normalize_datetime(task.created_at)
    else:
        # 降级处理：返回最小可能时间
        return datetime.min

@dataclass
class GlobalTask:
    """Global task information that persists across page refreshes"""
    task_id: str
    session_id: str
    user_id: str
    task_description: str
    status: str  # running, completed, error, stopped
    created_at: datetime
    last_activity: datetime
    config: Dict
    thread_id: Optional[str] = None
    error_message: Optional[str] = None
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    script_id: Optional[str] = None  # 在数据库中存储为UUID，Python中使用字符串

    @property
    def global_task_id(self) -> str:
        """向后兼容的属性，返回task_id"""
        return self.task_id

    def to_dict(self) -> Dict:
        """转换为字典，处理datetime序列化"""
        data = asdict(self)
        # 处理datetime对象
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data['last_activity'], datetime):
            data['last_activity'] = data['last_activity'].isoformat()
        if data['end_time'] and isinstance(data['end_time'], datetime):
            data['end_time'] = data['end_time'].isoformat()

        # 添加global_task_id用于向后兼容
        data['global_task_id'] = self.global_task_id
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'GlobalTask':
        """从字典创建对象，处理datetime反序列化和字段过滤"""
        # 1. 获取dataclass定义的所有有效字段
        valid_fields = {f.name for f in dataclasses.fields(cls)}

        # 2. 过滤字典,只保留有效字段
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        # 3. 记录被过滤的字段(用于调试)
        extra_fields = set(data.keys()) - valid_fields
        if extra_fields:
            logger.debug(f"过滤数据库额外字段: {extra_fields}")

        # 4. 类型转换 - datetime字段
        if 'created_at' in filtered_data and isinstance(filtered_data['created_at'], str):
            filtered_data['created_at'] = datetime.fromisoformat(filtered_data['created_at'])
        if 'last_activity' in filtered_data and isinstance(filtered_data['last_activity'], str):
            filtered_data['last_activity'] = datetime.fromisoformat(filtered_data['last_activity'])
        if filtered_data.get('end_time') and isinstance(filtered_data['end_time'], str):
            filtered_data['end_time'] = datetime.fromisoformat(filtered_data['end_time'])

        # 4.1 时区标准化 - 确保所有datetime对象都是无时区的
        for field in ['created_at', 'last_activity', 'end_time']:
            if field in filtered_data and isinstance(filtered_data[field], datetime):
                filtered_data[field] = normalize_datetime(filtered_data[field])

        # 5. 数据修复 - 自动修复缺失的可选字段
        if 'last_activity' not in filtered_data and 'created_at' in filtered_data:
            filtered_data['last_activity'] = filtered_data['created_at']
            logger.debug(f"自动修复: last_activity字段缺失,设置为created_at")

        # global_task_id现在是property，不需要特殊处理

        # 6. 创建对象
        try:
            return cls(**filtered_data)
        except TypeError as e:
            logger.error(f"创建GlobalTask失败: {e}")
            logger.error(f"数据: {filtered_data}")
            raise

    # 兼容旧API
    @property
    def global_task_id(self) -> str:
        return self.task_id

    @property
    def task(self) -> str:
        return self.task_description

    @property
    def error(self) -> Optional[str]:
        return self.error_message

    @property
    def start_time(self) -> datetime:
        return self.created_at

@dataclass
class FileInfo:
    """本地截图文件信息"""
    path: str           # 本地文件路径
    timestamp: datetime # 文件创建时间
    size: int          # 文件大小
    name: str          # 文件名
    match_score: float = 0.0  # 匹配度评分
    url: Optional[str] = None  # Web可访问URL


class LocalFileScanner:
    """本地文件扫描器 - 支持LRU缓存和性能优化"""

    def __init__(self, screenshots_dir: str = "static/screenshots", cache_timeout: int = 300):
        self.screenshots_dir = screenshots_dir
        self.cache_timeout = cache_timeout
        self._cache = {}
        self._cache_timestamp = 0
        self._scan_lock = threading.Lock()
        self._performance_stats = {
            'scans_count': 0,
            'cache_hits': 0,
            'total_scan_time': 0.0,
            'avg_scan_time': 0.0
        }

        # 配置参数
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置参数"""
        return {
            # 基础配置
            'enabled': os.getenv('SCREENSHOT_FALLBACK_ENABLED', 'true').lower() == 'true',
            'screenshots_dir': os.getenv('SCREENSHOT_DIR', self.screenshots_dir),
            'cache_timeout': int(os.getenv('SCREENSHOT_CACHE_TIMEOUT', str(self.cache_timeout))),

            # 性能配置
            'max_files': int(os.getenv('SCREENSHOT_MAX_FILES', '50')),
            'time_window_minutes': int(os.getenv('SCREENSHOT_TIME_WINDOW', '10')),
            'scan_batch_size': int(os.getenv('SCREENSHOT_SCAN_BATCH_SIZE', '100')),

            # 功能开关
            'enable_lru_cache': os.getenv('SCREENSHOT_ENABLE_LRU_CACHE', 'true').lower() == 'true',
            'enable_performance_monitoring': os.getenv('SCREENSHOT_ENABLE_PERF_MONITOR', 'true').lower() == 'true',
            'enable_async_scan': os.getenv('SCREENSHOT_ENABLE_ASYNC', 'false').lower() == 'true',

            # 调试配置
            'debug_mode': os.getenv('SCREENSHOT_DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('SCREENSHOT_LOG_LEVEL', 'INFO')
        }

    def is_enabled(self) -> bool:
        """检查功能是否启用"""
        return self.config['enabled']

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(new_config)
        logger.info(f"[LocalFileScanner] 配置已更新: {new_config}")

    def scan_screenshots(self) -> List[FileInfo]:
        """扫描本地截图文件 - 带性能监控和缓存"""
        # 检查功能是否启用
        if not self.is_enabled():
            if self.config['debug_mode']:
                logger.debug("[LocalFileScanner] 本地截图回退功能已禁用")
            return []

        current_time = time.time()
        scan_start_time = time.time()

        # 更新性能统计
        if self.config['enable_performance_monitoring']:
            self._performance_stats['scans_count'] += 1

        # 检查缓存
        if (current_time - self._cache_timestamp < self.cache_timeout and
            '_files' in self._cache):
            self._performance_stats['cache_hits'] += 1
            cache_hit_rate = (self._performance_stats['cache_hits'] /
                            self._performance_stats['scans_count']) * 100
            logger.debug(f"[LocalFileScanner] 缓存命中: {len(self._cache['_files'])} 个文件, "
                        f"命中率: {cache_hit_rate:.1f}%")
            return self._cache['_files']

        # 使用线程锁防止并发扫描
        with self._scan_lock:
            # 双重检查锁定模式
            if (current_time - self._cache_timestamp < self.cache_timeout and
                '_files' in self._cache):
                return self._cache['_files']

            files = []
            screenshots_path = Path(self.screenshots_dir)

            if not screenshots_path.exists():
                logger.warning(f"[LocalFileScanner] 截图目录不存在: {self.screenshots_dir}")
                return []

            try:
                # 使用os.scandir提高性能
                scan_start = time.time()
                with os.scandir(screenshots_dir) as entries:
                    for entry in entries:
                        if (entry.is_file() and
                            entry.name.startswith('screenshot_') and
                            entry.name.endswith('.png')):
                            try:
                                file_path = Path(entry.path)
                                file_info = self._parse_filename(file_path)
                                if file_info:
                                    # 添加文件大小信息
                                    file_info.size = entry.stat().st_size
                                    files.append(file_info)
                            except Exception as file_error:
                                logger.warning(f"[LocalFileScanner] 解析文件失败 {entry.name}: {file_error}")
                                continue

                scan_time = time.time() - scan_start

                # 按时间排序
                files.sort(key=lambda x: x.timestamp)

                # 缓存结果
                self._cache['_files'] = files
                self._cache_timestamp = current_time
                self._cache['_scan_time'] = scan_time

                # 更新性能统计
                self._performance_stats['total_scan_time'] += scan_time
                self._performance_stats['avg_scan_time'] = (
                    self._performance_stats['total_scan_time'] /
                    self._performance_stats['scans_count']
                )

                cache_hit_rate = ((self._performance_stats['scans_count'] - 1 - self._performance_stats['cache_hits']) /
                                max(1, self._performance_stats['scans_count'] - 1)) * 100

                logger.info(f"[LocalFileScanner] 扫描完成: {len(files)} 个截图文件, "
                          f"耗时: {scan_time:.3f}s, 缓存命中率: {cache_hit_rate:.1f}%")

                # 性能警告
                if scan_time > 2.0:
                    logger.warning(f"[LocalFileScanner] 扫描性能警告: 耗时 {scan_time:.3f}s, "
                                 f"文件数量: {len(files)}")

            except Exception as e:
                logger.error(f"[LocalFileScanner] 扫描失败: {e}")
                return []

        return files

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            **self._performance_stats,
            'cache_hit_rate': (self._performance_stats['cache_hits'] /
                             max(1, self._performance_stats['scans_count'])) * 100,
            'cache_valid': (time.time() - self._cache_timestamp < self.cache_timeout),
            'cached_files_count': len(self._cache.get('_files', [])),
            'last_scan_time': self._cache.get('_scan_time', 0)
        }

    def clear_cache(self):
        """清除缓存"""
        with self._scan_lock:
            self._cache.clear()
            self._cache_timestamp = 0
            logger.info("[LocalFileScanner] 缓存已清除")

    @lru_cache(maxsize=128)
    def _cached_parse_filename(self, filename: str, mtime: float) -> Optional[FileInfo]:
        """带LRU缓存的文件名解析"""
        file_path = Path(self.screenshots_dir) / filename
        return self._parse_filename(file_path)

    def _parse_filename(self, file_path: Path) -> Optional[FileInfo]:
        """解析文件名提取时间戳信息"""
        # 格式: screenshot_20251214_222529_098_9fa22334.png
        pattern = r"screenshot_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(\d{3})_"
        match = re.search(pattern, file_path.name)

        if match:
            try:
                year, month, day, hour, minute, second, millisecond = map(int, match.groups())
                timestamp = datetime(year, month, day, hour, minute, second, millisecond * 1000)

                # 获取文件大小
                try:
                    size = file_path.stat().st_size
                except OSError:
                    size = 0

                return FileInfo(
                    path=str(file_path),
                    timestamp=timestamp,
                    size=size,
                    name=file_path.name
                )
            except ValueError as e:
                logger.warning(f"[LocalFileScanner] 文件名解析失败: {file_path.name} - {e}")

        return None


class ScreenshotMatcher:
    """截图匹配算法"""

    def __init__(self, time_window_minutes: int = 10):
        self.time_window = timedelta(minutes=time_window_minutes)
        logger.info(f"[ScreenshotMatcher] 初始化，时间窗口: {time_window_minutes}分钟")

    def match_screenshots_to_task(self, task_info: dict, local_files: List[FileInfo]) -> List[FileInfo]:
        """将本地截图文件匹配到任务"""
        if not task_info or not local_files:
            return []

        task_created = task_info.get('created_at')
        task_completed = task_info.get('completed_at')

        if not task_created:
            logger.warning(f"[ScreenshotMatcher] 任务缺少创建时间: {task_info.get('task_id')}")
            return []

        # 解析任务时间
        try:
            if isinstance(task_created, str):
                start_time = datetime.fromisoformat(task_created.replace('Z', '+00:00'))
            else:
                start_time = task_created

            if task_completed:
                if isinstance(task_completed, str):
                    end_time = datetime.fromisoformat(task_completed.replace('Z', '+00:00'))
                else:
                    end_time = task_completed
            else:
                end_time = datetime.now()

            # 确保时间对象有时区信息
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=None)  # 移除时区信息，与文件时间保持一致
            else:
                start_time = start_time.replace(tzinfo=None)  # 转换为无时区时间

            if end_time.tzinfo is not None:
                end_time = end_time.replace(tzinfo=None)

        except Exception as e:
            logger.error(f"[ScreenshotMatcher] 时间解析失败: {e}")
            return []

        # 扩展时间窗口
        extended_start = start_time - self.time_window
        extended_end = end_time + self.time_window

        logger.debug(f"[ScreenshotMatcher] 任务时间范围: {start_time} - {end_time}")
        logger.debug(f"[ScreenshotMatcher] 扩展匹配范围: {extended_start} - {extended_end}")

        # 匹配在时间范围内的截图
        matched_files = []
        for file_info in local_files:
            if extended_start <= file_info.timestamp <= extended_end:
                file_info.match_score = self._calculate_match_score(
                    file_info.timestamp, start_time, end_time
                )
                matched_files.append(file_info)

        # 按匹配度排序
        matched_files.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"[ScreenshotMatcher] 匹配结果: {len(matched_files)} 个文件")

        return matched_files

    def _calculate_match_score(self, file_timestamp: datetime,
                              task_start: datetime, task_end: datetime) -> float:
        """计算文件与任务的匹配度"""
        if task_start <= file_timestamp <= task_end:
            return 1.0  # 完美匹配：在任务执行期间

        # 计算到任务时间范围的距离
        if file_timestamp < task_start:
            distance = (task_start - file_timestamp).total_seconds()
        else:
            distance = (file_timestamp - task_end).total_seconds()

        # 距离越近分数越高
        max_distance = self.time_window.total_seconds()
        score = max(0, 1 - (distance / max_distance))

        return score


class PathConverter:
    """路径转换器"""

    def __init__(self, base_url: str = "/static/screenshots"):
        self.base_url = base_url.rstrip('/')

    def convert_to_web_url(self, local_path: str) -> str:
        """将本地文件路径转换为Web URL"""
        filename = Path(local_path).name
        return f"{self.base_url}/{filename}"

    def validate_file_exists(self, local_path: str) -> bool:
        """验证文件是否存在且可访问"""
        return Path(local_path).exists() and Path(local_path).is_file()


class SupabaseTaskManager:
    """基于Supabase的全局任务管理器"""

    # 有效的状态枚举值
    VALID_STATUSES = {'running', 'completed', 'error', 'stopped'}

    # 必需字段列表
    REQUIRED_FIELDS = {
        'task_id', 'session_id', 'user_id', 'task_description',
        'status', 'created_at', 'last_activity', 'config'
    }

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase配置未找到，请检查环境变量SUPABASE_URL和SUPABASE_SECRET_KEY")

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.tasks: Dict[str, GlobalTask] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

        # 尝试创建tasks表（如果不存在）
        self._create_table_if_not_exists()

        # 加载现有任务
        self.load_tasks()

    def _create_table_if_not_exists(self):
        """创建tasks表（如果不存在）"""
        try:
            # 检查表是否存在
            result = self.supabase.table('tasks').select('id').limit(1).execute()
            # 如果能成功执行，说明表存在
            return
        except Exception as e:
            print(f"检查tasks表时出错: {e}")
            # 表可能不存在，尝试创建
            try:
                # 使用Supabase的RPC功能创建表
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    task_id TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    last_activity TIMESTAMPTZ NOT NULL,
                    config JSONB NOT NULL,
                    thread_id TEXT,
                    error_message TEXT,
                    end_time TIMESTAMPTZ,
                    result TEXT,
                    script_id TEXT REFERENCES scripts(id)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
                CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_script_id ON tasks(script_id);
                """

                # 这里需要通过Supabase的SQL编辑器手动创建表，或者使用Supabase Dashboard
                print("请通过Supabase Dashboard创建tasks表，SQL如下：")
                print(create_table_sql)

            except Exception as create_error:
                print(f"创建表时出错: {create_error}")

    def _validate_task_data(self, data: Dict, task_id: str = None) -> tuple[bool, Optional[str]]:
        """
        验证任务数据的完整性和正确性

        Args:
            data: 任务数据字典
            task_id: 任务ID(用于日志)

        Returns:
            (is_valid, error_message): 验证是否通过和错误信息
        """
        task_id = task_id or data.get('task_id', 'unknown')

        # 1. 检查必需字段是否存在
        missing_fields = self.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            return False, f"缺失必需字段: {', '.join(missing_fields)}"

        # 2. 验证status字段的枚举值
        status = data.get('status')
        if status not in self.VALID_STATUSES:
            return False, f"非法的status值: '{status}', 必须是以下之一: {', '.join(self.VALID_STATUSES)}"

        # 3. 验证datetime字段格式
        datetime_fields = ['created_at', 'last_activity', 'end_time']
        for field in datetime_fields:
            value = data.get(field)
            if value is None and field in ['end_time']:  # 可选字段
                continue

            if value is None:
                return False, f"datetime字段 '{field}' 不能为空"

            # 如果是字符串,尝试解析
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                except (ValueError, TypeError) as e:
                    return False, f"datetime字段 '{field}' 格式错误: {e}"
            elif not isinstance(value, datetime):
                return False, f"datetime字段 '{field}' 类型错误: 期望datetime或ISO字符串, 实际为{type(value).__name__}"

        # 4. 验证config字段
        config = data.get('config')
        if config is None:
            return False, "config字段不能为空"

        # 如果config是字符串,尝试解析为JSON
        if isinstance(config, str):
            try:
                json.loads(config)
            except json.JSONDecodeError as e:
                return False, f"config字段JSON格式错误: {e}"
        elif not isinstance(config, dict):
            return False, f"config字段类型错误: 期望dict或JSON字符串, 实际为{type(config).__name__}"

        # 5. 验证字符串字段非空
        string_fields = ['task_id', 'session_id', 'user_id', 'task_description']
        for field in string_fields:
            value = data.get(field)
            if not value or not isinstance(value, str) or not value.strip():
                return False, f"字段 '{field}' 不能为空字符串"

        return True, None

    def add_task(self, task: GlobalTask) -> bool:
        """添加任务到数据库"""
        try:
            with self.lock:
                # 添加到内存
                # global_task_id已经在__post_init__中自动处理了

                # 使用task_id作为内存存储的主键
                self.tasks[task.task_id] = task

                # 添加到数据库
                task_dict = task.to_dict()
                result = self.supabase.table('tasks').insert(task_dict).execute()

                if result.data:
                    print(f"任务已添加到数据库: {task.task_id}")
                    return True
                else:
                    print(f"添加任务到数据库失败: {task.task_id}")
                    return False

        except Exception as e:
            print(f"添加任务时出错: {e}")
            return False

    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务状态，支持task_id或global_task_id"""
        try:
            with self.lock:
                # 尝试通过task_id查找
                task = None
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                else:
                    # 尝试通过global_task_id查找
                    for t in self.tasks.values():
                        if t.global_task_id == task_id or t.task_id == task_id:
                            task = t
                            break

                if not task:
                    return False

                # 更新内存中的任务
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

                # 更新数据库中的任务
                update_data = {k: v for k, v in kwargs.items() if k != 'global_task_id'}

                # 处理datetime对象
                if 'start_time' in update_data and isinstance(update_data['start_time'], datetime):
                    update_data['start_time'] = update_data['start_time'].isoformat()
                if 'end_time' in update_data and update_data['end_time'] and isinstance(update_data['end_time'], datetime):
                    update_data['end_time'] = update_data['end_time'].isoformat()
                if 'last_activity' in update_data and isinstance(update_data['last_activity'], datetime):
                    update_data['last_activity'] = update_data['last_activity'].isoformat()

                result = self.supabase.table('tasks').update(update_data).eq('task_id', task.task_id).execute()

                if result.data:
                    logger.debug(f"Task updated successfully: {task.task_id}, affected rows: {len(result.data)}")
                    return True
                else:
                    logger.warning(f"Task update returned no data for task_id: {task.task_id}")
                    return False

        except Exception as e:
            print(f"更新任务时出错: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[GlobalTask]:
        """获取指定任务，支持task_id或global_task_id"""
        with self.lock:
            # 尝试直接通过task_id查找
            if task_id in self.tasks:
                return self.tasks[task_id]

            # 尝试通过global_task_id查找
            for task in self.tasks.values():
                if task.global_task_id == task_id or task.task_id == task_id:
                    return task

            return None

    def get_all_tasks(self) -> List[GlobalTask]:
        """获取所有任务（按创建时间降序）"""
        with self.lock:
            # 按创建时间降序排列 - 使用时区安全的排序
            return sorted(self.tasks.values(), key=safe_datetime_sort_key, reverse=True)

    def get_running_tasks(self) -> List[GlobalTask]:
        """获取正在运行的任务"""
        with self.lock:
            return [task for task in self.tasks.values() if task.status == 'running']

    def create_task(self, task_id: str, session_id: str, user_id: str,
                   task_description: str, config: Dict) -> GlobalTask:
        """Create a new global task"""
        # 使用无时区的UTC时间保持一致性
        now = normalize_datetime(datetime.utcnow())
        task = GlobalTask(
            task_id=task_id,
            session_id=session_id,
            user_id=user_id,
            task_description=task_description,
            status="running",
            created_at=now,
            last_activity=now,
            config=config
        )
        self.add_task(task)
        return task

    def update_task_status(self, task_id: str, status: str, error_message: str = None, result: str = None):
        """Update task status"""
        # 使用无时区的UTC时间保持一致性
        now = normalize_datetime(datetime.utcnow())
        update_data = {'status': status, 'last_activity': now}
        if error_message:
            update_data['error_message'] = error_message
        if result:
            update_data['result'] = result
        if status in ['completed', 'stopped', 'error']:
            update_data['end_time'] = now

        return self.update_task(task_id, **update_data)

    def get_tasks_by_session(self, session_id: str) -> List[GlobalTask]:
        """Get tasks by session ID（按创建时间降序）"""
        with self.lock:
            # 过滤并按创建时间降序排列 - 使用时区安全的排序
            return sorted(
                [task for task in self.tasks.values() if task.session_id == session_id],
                key=safe_datetime_sort_key,
                reverse=True
            )

    def stop_task(self, task_id: str) -> bool:
        """Stop a task, supports task_id or global_task_id"""
        try:
            with self.lock:
                # 查找任务
                task = self.get_task(task_id)
                if not task:
                    return False

                # Update task status
                self.update_task_status(task.task_id, "stopped")

                # Stop thread if exists
                if task.task_id in self.active_threads:
                    try:
                        thread = self.active_threads[task.task_id]
                        # 由于Python线程不能直接强制停止，我们只能标记状态
                        # 在实际的任务执行中需要检查停止标志
                        print(f"标记任务停止: {task.task_id}")
                    except Exception as thread_error:
                        print(f"停止线程时出错: {thread_error}")
                    finally:
                        del self.active_threads[task.task_id]

                return True

        except Exception as e:
            print(f"停止任务时出错: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务，支持task_id或global_task_id"""
        try:
            with self.lock:
                # 查找任务
                task = self.get_task(task_id)
                if not task:
                    return False

                # 从内存中删除
                del self.tasks[task.task_id]

                # 从数据库中删除
                result = self.supabase.table('tasks').delete().eq('task_id', task.task_id).execute()

                if result.data:
                    print(f"任务已删除: {task.task_id}")
                    return True
                else:
                    print(f"删除任务失败: {task.task_id}")
                    return False

        except Exception as e:
            print(f"删除任务时出错: {e}")
            return False

    def load_tasks(self) -> bool:
        """从数据库加载所有任务,弹性处理单个任务加载失败"""
        import time
        start_time = time.time()

        try:
            logger.info("正在从Supabase加载任务...")

            # 从数据库获取所有任务
            result = self.supabase.table('tasks').select('*').order('created_at', desc=True).execute()

            if not result.data:
                logger.info("数据库中没有任务")
                return True

            # 统计信息
            total_count = len(result.data)
            success_count = 0
            skip_count = 0
            skipped_tasks = []

            with self.lock:
                self.tasks.clear()

                for task_data in result.data:
                    task_id = task_data.get('task_id', 'unknown')

                    try:
                        # 1. 验证任务数据完整性
                        is_valid, error_msg = self._validate_task_data(task_data, task_id)
                        if not is_valid:
                            skip_count += 1
                            skipped_tasks.append((task_id, f"数据验证失败: {error_msg}"))
                            logger.warning(f"跳过任务 {task_id}: 数据验证失败 - {error_msg}")
                            continue

                        # 2. 尝试加载单个任务
                        task = GlobalTask.from_dict(task_data)
                        self.tasks[task.task_id] = task
                        success_count += 1

                    except Exception as e:
                        # 记录失败的任务,但继续加载其他任务
                        skip_count += 1
                        error_msg = str(e)
                        skipped_tasks.append((task_id, error_msg))

                        logger.warning(
                            f"跳过任务 {task_id}: {error_msg[:100]}"
                        )

                        # 记录详细错误到debug级别
                        logger.debug(f"任务数据: {task_data}")
                        logger.debug(f"完整错误: {e}", exc_info=True)

            # 输出加载统计
            duration = time.time() - start_time
            logger.info(
                f"任务加载完成: 成功 {success_count}/{total_count}, "
                f"跳过 {skip_count}, 耗时 {duration:.2f}秒"
            )

            # 如果有跳过的任务,输出汇总
            if skipped_tasks:
                logger.warning(f"以下{len(skipped_tasks)}个任务加载失败:")
                for tid, err in skipped_tasks[:5]:  # 最多显示5个
                    logger.warning(f"  - {tid}: {err[:80]}")
                if len(skipped_tasks) > 5:
                    logger.warning(f"  ... 还有{len(skipped_tasks)-5}个任务")

            # 性能警告
            if duration > 3.0:
                logger.warning(f"⚠️  任务加载耗时过长: {duration:.2f}秒")

            return True

        except Exception as e:
            logger.error(f"加载任务时发生严重错误: {e}", exc_info=True)
            logger.error("应用将以空任务列表启动")
            # 如果数据库连接失败，使用空的任务列表
            with self.lock:
                self.tasks.clear()
            return False

    def save_tasks(self) -> bool:
        """保存所有任务到数据库（实际上任务是实时保存的，这里是为了兼容性）"""
        # 由于Supabase是实时保存的，这个方法主要是为了兼容性
        return True

    def register_thread(self, task_id: str, thread: threading.Thread):
        """注册任务线程，支持task_id或global_task_id"""
        with self.lock:
            self.active_threads[task_id] = thread

    def unregister_thread(self, task_id: str):
        """取消注册任务线程，支持task_id或global_task_id"""
        with self.lock:
            if task_id in self.active_threads:
                del self.active_threads[task_id]

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """清理旧任务，返回删除的任务数量"""
        try:
            cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)

            # 从数据库删除旧任务
            result = self.supabase.table('tasks').delete().lt('created_at', cutoff_date.isoformat()).execute()

            if result.data:
                deleted_count = len(result.data)
                print(f"清理了 {deleted_count} 个旧任务")

                # 重新加载任务
                self.load_tasks()
                return deleted_count
            else:
                print("没有需要清理的旧任务")
                return 0

        except Exception as e:
            print(f"清理旧任务时出错: {e}")
            return 0

# Step data management methods
    def save_step(self, step_data: Dict) -> Optional[str]:
        """保存单个步骤数据"""
        try:
            # 尝试序列化数据以提前发现问题
            import json
            try:
                json_str = json.dumps(step_data, default=str)
                logger.debug(f"Step data is serializable: {len(json_str)} chars")
            except (TypeError, ValueError) as e:
                logger.error(f"Step data is not serializable: {e}")
                # 使用 default=str 强制转换
                step_data = json.loads(json.dumps(step_data, default=str))

            result = self.supabase.table('task_steps').insert(step_data).execute()

            if result.data:
                step_id = result.data[0].get('id')
                logger.debug(f"Step saved with ID: {step_id}")
                return step_id
            else:
                logger.error(f"Failed to save step: {step_data.get('task_id')}")
                return None

        except Exception as e:
            logger.error(f"Error saving step: {e}")
            logger.error(f"Step data type: {type(step_data)}")
            if isinstance(step_data, dict):
                logger.error(f"Step data keys: {list(step_data.keys())}")
            return None

    def save_steps_batch(self, steps_data: List[Dict]) -> bool:
        """批量保存步骤数据"""
        try:
            result = self.supabase.table('task_steps').insert(steps_data).execute()

            if result.data:
                logger.info(f"Batch saved {len(steps_data)} steps")
                return True
            else:
                logger.error("Failed to batch save steps")
                return False

        except Exception as e:
            logger.error(f"Error batch saving steps: {e}")
            return False

    def get_task_steps(self, task_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取任务的所有步骤"""
        try:
            query = self.supabase.table('task_steps')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('step_number', desc=False)

            if limit:
                query = query.limit(limit)

            result = query.execute()

            if result.data:
                return result.data
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting task steps: {e}")
            return []

    def save_step_screenshot(self, screenshot_data: Dict) -> bool:
        """保存步骤截图信息"""
        try:
            result = self.supabase.table('step_screenshots').insert(screenshot_data).execute()

            if result.data:
                logger.debug(f"Screenshot saved: {screenshot_data.get('id')}")
                return True
            else:
                logger.error(f"Failed to save screenshot: {screenshot_data.get('id')}")
                return False

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return False

    def get_step_screenshots(self, task_id: str) -> List[Dict]:
        """获取任务的所有截图"""
        try:
            result = self.supabase.table('step_screenshots')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('created_at', desc=False)\
                .execute()

            if result.data:
                return result.data
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting step screenshots: {e}")
            return []

    def update_task_step_statistics(self, task_id: str, stats: Dict) -> bool:
        """更新任务步骤统计信息"""
        try:
            update_data = {
                'last_activity': datetime.now().isoformat(),
                'has_detailed_steps': True
            }
            update_data.update(stats)

            result = self.supabase.table('tasks')\
                .update(update_data)\
                .eq('task_id', task_id)\
                .execute()

            if result.data:
                logger.debug(f"Task statistics updated: {task_id}")
                return True
            else:
                logger.error(f"Failed to update task statistics: {task_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating task statistics: {e}")
            return False

    def get_step_report_data(self, task_id: str) -> Dict:
        """获取步骤报告数据"""
        try:
            logger.info(f"[DataExtraction] 开始获取任务报告数据: {task_id}")

            # Get task info
            task_result = self.supabase.table('tasks')\
                .select('*')\
                .eq('task_id', task_id)\
                .execute()

            task_data = task_result.data[0] if task_result.data else None
            logger.info(f"[DataExtraction] 任务信息: {task_data}")

            # Get steps
            steps_result = self.supabase.table('task_steps')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('step_number', desc=False)\
                .execute()

            # Get screenshots from step_screenshots table
            screenshots_result = self.supabase.table('step_screenshots')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('created_at', desc=False)\
                .execute()

            # Extract screenshots from steps that have screenshot_path
            step_screenshots = []
            if steps_result.data:
                for step in steps_result.data:
                    if step.get('screenshot_path') or step.get('screenshot_url'):
                        screenshot_data = {
                            'screenshot_path': step.get('screenshot_path'),
                            'screenshot_url': step.get('screenshot_url'),
                            'created_at': step.get('created_at') or step.get('timestamp'),
                            'step_number': step.get('step_number'),
                            'step_type': step.get('step_type') or step.get('action'),
                            'step_id': step.get('step_id'),
                            'task_id': step.get('task_id'),
                            'source': 'task_steps'
                        }
                        step_screenshots.append(screenshot_data)
                        logger.info(f"[DataExtraction] 从步骤中提取截图: 步骤{step.get('step_number')} -> {step.get('screenshot_path')}")

            # Combine screenshots from both sources
            all_screenshots = []
            if screenshots_result.data:
                all_screenshots.extend(screenshots_result.data)
                logger.info(f"[DataExtraction] 从step_screens表获取: {len(screenshots_result.data)} 张截图")

            if step_screenshots:
                all_screenshots.extend(step_screenshots)
                logger.info(f"[DataExtraction] 从task_steps提取: {len(step_screenshots)} 张截图")

            # 本地文件回退：当数据库无截图数据时，扫描本地文件
            if not all_screenshots and task_data:
                logger.info(f"[DataExtraction] 数据库无截图数据，尝试本地文件回退")
                local_screenshots = self._get_local_screenshots_fallback(task_id, task_data)
                if local_screenshots:
                    all_screenshots.extend(local_screenshots)
                    logger.info(f"[DataExtraction] 本地文件回退成功: {len(local_screenshots)} 张截图")
                else:
                    logger.info(f"[DataExtraction] 本地文件回退: 未找到匹配的截图")

            # Log statistics
            logger.info(f"[DataExtraction] 统计信息:")
            logger.info(f"  - 任务ID: {task_id}")
            logger.info(f"  - 步骤数量: {len(steps_result.data) if steps_result.data else 0}")
            logger.info(f"  - 截图数量(独立表): {len(screenshots_result.data) if screenshots_result.data else 0}")
            logger.info(f"  - 截图数量(步骤中): {len(step_screenshots)}")
            logger.info(f"  - 截图数量(本地回退): {len([s for s in all_screenshots if s.get('source') == 'local_fallback'])}")
            logger.info(f"  - 截图总数: {len(all_screenshots)}")

            return {
                'task': task_data,
                'steps': steps_result.data if steps_result.data else [],
                'screenshots': all_screenshots
            }

        except Exception as e:
            logger.error(f"Error getting step report data: {e}")
            logger.exception(f"[DataExtraction] 获取任务报告数据失败: {task_id}")

            # 返回部分数据而不是完全失败
            task_data = task_data if 'task_data' in locals() else None
            steps_data = steps_result.data if 'steps_result' in locals() and hasattr(steps_result, 'data') else []
            screenshots_data = all_screenshots if 'all_screenshots' in locals() else []

            logger.warning(f"[DataExtraction] 返回部分数据: 任务={task_data is not None}, 步骤={len(steps_data)}, 截图={len(screenshots_data)}")

            return {
                'task': task_data,
                'steps': steps_data,
                'screenshots': screenshots_data,
                'error': True,
                'error_message': str(e)
            }

    def _get_local_screenshots_fallback(self, task_id: str, task_info: dict) -> List[dict]:
        """本地文件回退获取截图 - 增强错误处理和日志记录"""
        if not task_info:
            logger.warning(f"[LocalFile] 任务信息为空，无法进行本地文件回退: {task_id[:8]}")
            return []

        fallback_start_time = time.time()
        error_stats = {
            'scan_errors': 0,
            'match_errors': 0,
            'path_errors': 0,
            'validation_errors': 0
        }

        try:
            logger.info(f"[LocalFile] 开始本地文件回退: 任务 {task_id[:8]}...")

            # 1. 扫描本地文件
            scanner = LocalFileScanner()

            # 检查扫描器是否启用
            if not scanner.is_enabled():
                logger.info(f"[LocalFile] 本地文件回退功能已禁用")
                return []

            local_files = scanner.scan_screenshots()

            if not local_files:
                logger.warning(f"[LocalFile] 未找到本地截图文件，目录: {scanner.screenshots_dir}")
                self._log_fallback_statistics(task_id, 0, fallback_start_time, error_stats)
                return []

            logger.info(f"[LocalFile] 扫描到 {len(local_files)} 个本地截图文件")

            # 记录性能统计
            if scanner.config['enable_performance_monitoring']:
                perf_stats = scanner.get_performance_stats()
                logger.debug(f"[LocalFile] 扫描器性能统计: {perf_stats}")

            # 2. 匹配到任务
            try:
                matcher = ScreenshotMatcher()
                matched_files = matcher.match_screenshots_to_task(task_info, local_files)
            except Exception as match_error:
                error_stats['match_errors'] += 1
                logger.error(f"[LocalFile] 截图匹配失败: {match_error}")
                self._log_fallback_statistics(task_id, 0, fallback_start_time, error_stats)
                return []

            if not matched_files:
                logger.warning(f"[LocalFile] 未找到与任务匹配的截图，任务时间范围可能不匹配")
                self._log_fallback_statistics(task_id, 0, fallback_start_time, error_stats)
                return []

            logger.info(f"[LocalFile] 匹配到 {len(matched_files)} 个相关截图文件")

            # 3. 转换路径和格式
            try:
                converter = PathConverter()
                result = []

                # 限制返回的截图数量
                max_screenshots = scanner.config['max_files']
                processed_files = 0
                valid_files = 0

                for file_info in matched_files[:max_screenshots]:
                    processed_files += 1
                    try:
                        # 验证文件存在性
                        if converter.validate_file_exists(file_info.path):
                            # 验证文件可读性
                            if self._validate_screenshot_file(file_info.path):
                                screenshot_data = {
                                    'screenshot_path': file_info.path,
                                    'screenshot_url': converter.convert_to_web_url(file_info.path),
                                    'created_at': file_info.timestamp.isoformat(),
                                    'file_size': file_info.size,
                                    'match_score': file_info.match_score,
                                    'source': 'local_fallback',
                                    'task_id': task_id,
                                    'step_number': None,  # 本地文件无法确定步骤号
                                    'step_id': None
                                }
                                result.append(screenshot_data)
                                valid_files += 1
                            else:
                                error_stats['validation_errors'] += 1
                                logger.warning(f"[LocalFile] 文件验证失败: {file_info.path}")
                        else:
                            error_stats['path_errors'] += 1
                            logger.warning(f"[LocalFile] 文件不存在: {file_info.path}")

                    except Exception as file_error:
                        error_stats['validation_errors'] += 1
                        logger.warning(f"[LocalFile] 处理文件时出错 {file_info.path}: {file_error}")
                        continue

                logger.info(f"[LocalFile] 文件处理完成: 处理 {processed_files} 个，有效 {valid_files} 个")

            except Exception as conversion_error:
                error_stats['path_errors'] += 1
                logger.error(f"[LocalFile] 路径转换失败: {conversion_error}")
                return []

            # 记录成功统计
            fallback_time = time.time() - fallback_start_time
            logger.info(f"[LocalFile] 回退成功: 返回 {len(result)} 张有效截图, 耗时: {fallback_time:.3f}s")
            self._log_fallback_statistics(task_id, len(result), fallback_start_time, error_stats)

            return result

        except Exception as e:
            fallback_time = time.time() - fallback_start_time
            logger.error(f"[LocalFile] 本地文件回退失败: {e}, 耗时: {fallback_time:.3f}s")
            logger.error(f"[LocalFile] 错误详情: {type(e).__name__}: {str(e)}")

            # 记录错误统计
            if scanner.config['debug_mode']:
                import traceback
                logger.debug(f"[LocalFile] 错误堆栈: {traceback.format_exc()}")

            self._log_fallback_statistics(task_id, 0, fallback_start_time, error_stats)
            return []

    def _validate_screenshot_file(self, file_path: str) -> bool:
        """验证截图文件是否有效"""
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return False

            # 检查文件大小
            file_size = path.stat().st_size
            if file_size == 0:
                return False

            # 检查文件扩展名
            if path.suffix.lower() != '.png':
                return False

            # 简单的文件头验证
            with open(path, 'rb') as f:
                header = f.read(8)
                # PNG文件头: \x89PNG\r\n\x1a\n
                if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                    return False

            return True
        except Exception as e:
            logger.debug(f"[LocalFile] 文件验证异常 {file_path}: {e}")
            return False

    def _log_fallback_statistics(self, task_id: str, result_count: int, start_time: float, error_stats: dict):
        """记录回退统计信息"""
        try:
            total_time = time.time() - start_time
            total_errors = sum(error_stats.values())

            logger.info(f"[LocalFile] 回退统计 - 任务 {task_id[:8]}:")
            logger.info(f"  - 执行时间: {total_time:.3f}s")
            logger.info(f"  - 返回截图: {result_count} 张")
            logger.info(f"  - 错误总数: {total_errors}")

            if total_errors > 0:
                logger.warning(f"[LocalFile] 错误分类: {error_stats}")

            # 性能警告
            if total_time > 3.0:
                logger.warning(f"[LocalFile] 性能警告: 回退耗时 {total_time:.3f}s")

        except Exception as log_error:
            logger.error(f"[LocalFile] 统计日志记录失败: {log_error}")
            logger.exception(f"[LocalFile] 错误详情")
            return []

    def cleanup_old_steps(self, days: int = 30) -> int:
        """清理旧步骤数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Delete old steps
            steps_result = self.supabase.table('task_steps')\
                .delete()\
                .lt('created_at', cutoff_date.isoformat())\
                .execute()

            # Delete old screenshots
            screenshots_result = self.supabase.table('step_screenshots')\
                .delete()\
                .lt('created_at', cutoff_date.isoformat())\
                .execute()

            deleted_steps = len(steps_result.data) if steps_result.data else 0
            deleted_screenshots = len(screenshots_result.data) if screenshots_result.data else 0

            logger.info(f"Cleaned up {deleted_steps} steps and {deleted_screenshots} screenshots")
            return deleted_steps + deleted_screenshots

        except Exception as e:
            logger.error(f"Error cleaning up old steps: {e}")
            return 0

    # Statistics and reporting methods
    def get_statistics(self, days: int = 30) -> Dict:
        """获取任务统计信息"""
        try:
            from datetime import datetime, timedelta, timezone

            # 计算时间范围
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 任务统计
            total_tasks_result = self.supabase.table('tasks')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .execute()

            completed_tasks_result = self.supabase.table('tasks')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .eq('status', 'completed')\
                .execute()

            failed_tasks_result = self.supabase.table('tasks')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .eq('status', 'failed')\
                .execute()

            # 步骤统计
            steps_result = self.supabase.table('task_steps')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .execute()

            successful_steps_result = self.supabase.table('task_steps')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .eq('success', True)\
                .execute()

            # 截图统计
            screenshots_result = self.supabase.table('step_screenshots')\
                .select('count', count='exact')\
                .gte('created_at', start_date)\
                .execute()

            return {
                "tasks": {
                    "total": total_tasks_result.count or 0,
                    "completed": completed_tasks_result.count or 0,
                    "failed": failed_tasks_result.count or 0,
                    "running": (total_tasks_result.count or 0) - (completed_tasks_result.count or 0) - (failed_tasks_result.count or 0)
                },
                "steps": {
                    "total": steps_result.count or 0,
                    "successful": successful_steps_result.count or 0,
                    "failed": (steps_result.count or 0) - (successful_steps_result.count or 0)
                },
                "screenshots": {
                    "total": screenshots_result.count or 0
                },
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "tasks": {"total": 0, "completed": 0, "failed": 0, "running": 0},
                "steps": {"total": 0, "successful": 0, "failed": 0},
                "screenshots": {"total": 0},
                "period_days": days,
                "error": str(e)
            }

  # Screenshot URL update methods
    def update_step_screenshot_url(self, step_id: str, local_path: str, remote_url: str) -> bool:
        """Update screenshot URLs for a step"""
        try:
            # Update task_steps table
            result1 = self.supabase.table('task_steps')\
                .update({'screenshot_url': remote_url})\
                .eq('step_id', step_id)\
                .execute()

            # Update step_screenshots table
            result2 = self.supabase.table('step_screenshots')\
                .update({'remote_url': remote_url})\
                .eq('screenshot_path', local_path)\
                .execute()

            if result1.data and result2.data:
                logger.info(f"Updated screenshot URLs for step: {step_id}")
                return True
            else:
                logger.error(f"Failed to update screenshot URLs for step: {step_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating screenshot URLs: {e}")
            return False

    def get_screenshot_with_fallback(self, task_id: str, step_id: str) -> Optional[Dict]:
        """Get screenshot with remote URL fallback to local path"""
        try:
            # First try to get from step_screenshots with remote_url
            result = self.supabase.table('step_screenshots')\
                .select('*')\
                .eq('task_id', task_id)\
                .eq('step_id', step_id)\
                .not_.is_('remote_url', 'null')\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            # Fallback to task_steps
            result = self.supabase.table('task_steps')\
                .select('screenshot_path', 'screenshot_url')\
                .eq('task_id', task_id)\
                .eq('step_id', step_id)\
                .not_.is_('screenshot_url', 'null')\
                .execute()

            if result.data and len(result.data) > 0:
                return {
                    'remote_url': result.data[0].get('screenshot_url'),
                    'screenshot_path': result.data[0].get('screenshot_path'),
                    'local_path': result.data[0].get('screenshot_path')
                }

            return None

        except Exception as e:
            logger.error(f"Error getting screenshot with fallback: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取任务和步骤统计信息"""
        try:
            statistics = {
                'tasks': {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'running': 0
                },
                'steps': {
                    'total': 0,
                    'successful': 0
                },
                'screenshots': {
                    'total': 0
                }
            }

            # 任务统计
            try:
                result = self.supabase.table('tasks').select('status', count='exact').execute()
                if result.data:
                    statistics['tasks']['total'] = result.count or 0

                # 各状态任务数量
                for status in ['completed', 'failed', 'running']:
                    result = self.supabase.table('tasks').select('status', count='exact').eq('status', status).execute()
                    if result.data:
                        statistics['tasks'][status] = result.count or 0

                logger.info(f"Task statistics: {statistics['tasks']}")

            except Exception as e:
                logger.error(f"Error getting task statistics: {e}")

            # 步骤统计
            try:
                result = self.supabase.table('task_steps').select('*', count='exact').execute()
                if result.data:
                    statistics['steps']['total'] = result.count or 0

                # 成功步骤数量
                result = self.supabase.table('task_steps').select('*', count='exact').eq('success', True).execute()
                if result.data:
                    statistics['steps']['successful'] = result.count or 0

                logger.info(f"Step statistics: {statistics['steps']}")

            except Exception as e:
                logger.error(f"Error getting step statistics: {e}")

            # 截图统计
            try:
                result = self.supabase.table('step_screenshots').select('*', count='exact').execute()
                if result.data:
                    statistics['screenshots']['total'] = result.count or 0

                logger.info(f"Screenshot statistics: {statistics['screenshots']}")

            except Exception as e:
                logger.error(f"Error getting screenshot statistics: {e}")

            return statistics

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def get_task_summary(self, limit: int = 10) -> Dict[str, Any]:
        """获取任务摘要统计"""
        try:
            summary = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'running_tasks': 0,
                'failed_tasks': 0,
                'average_duration': 0.0,
                'recent_tasks': []
            }

            # 基本统计
            try:
                result = self.supabase.table('tasks').select('*', count='exact').execute()
                if result.data:
                    summary['total_tasks'] = result.count or 0

                # 各状态任务数量
                for status in ['completed', 'running', 'failed']:
                    result = self.supabase.table('tasks').select('*', count='exact').eq('status', status).execute()
                    if result.data:
                        summary[f'{status}_tasks'] = result.count or 0

            except Exception as e:
                logger.error(f"Error getting task counts: {e}")

            # 平均执行时间
            try:
                result = self.supabase.table('tasks')\
                    .select('created_at', 'end_time')\
                    .eq('status', 'completed')\
                    .not_.is_('end_time', 'null')\
                    .execute()

                if result.data:
                    total_duration = 0
                    count = 0
                    for task in result.data:
                        try:
                            if task.get('created_at') and task.get('end_time'):
                                start = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                                end = datetime.fromisoformat(task['end_time'].replace('Z', '+00:00'))
                                duration = (end - start).total_seconds()
                                total_duration += duration
                                count += 1
                        except Exception as e:
                            logger.warning(f"Error calculating duration for task {task.get('task_id')}: {e}")

                    if count > 0:
                        summary['average_duration'] = total_duration / count

            except Exception as e:
                logger.error(f"Error calculating average duration: {e}")

            # 最近任务
            try:
                result = self.supabase.table('tasks')\
                    .select('*')\
                    .order('created_at', desc=True)\
                    .limit(limit)\
                    .execute()

                if result.data:
                    summary['recent_tasks'] = result.data

            except Exception as e:
                logger.error(f"Error getting recent tasks: {e}")

            logger.info(f"Task summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error getting task summary: {e}")
            return {}

# 导出主要类
__all__ = ['SupabaseTaskManager', 'GlobalTask']

if __name__ == "__main__":
    # 测试代码
    try:
        manager = SupabaseTaskManager()
        print("Supabase任务管理器初始化成功")

        # 测试创建任务
        test_task = GlobalTask(
            global_task_id=str(uuid.uuid4()),
            session_id="test_session",
            task="测试任务",
            status="running",
            start_time=datetime.now()
        )

        if manager.add_task(test_task):
            print("测试任务创建成功")

            # 测试获取任务
            loaded_task = manager.get_task(test_task.global_task_id)
            if loaded_task:
                print(f"任务加载成功: {loaded_task.task}")

            # 清理测试任务
            manager.delete_task(test_task.global_task_id)
            print("测试任务已删除")

    except Exception as e:
        print(f"测试失败: {e}")