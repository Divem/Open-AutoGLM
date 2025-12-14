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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client

# 配置日志
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 从环境变量获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SECRET_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

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

        # 5. 数据修复 - 自动修复缺失的可选字段
        if 'last_activity' not in filtered_data and 'created_at' in filtered_data:
            filtered_data['last_activity'] = filtered_data['created_at']
            logger.debug(f"自动修复: last_activity字段缺失,设置为created_at")

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
                self.tasks[task.global_task_id] = task

                # 添加到数据库
                task_dict = task.to_dict()
                result = self.supabase.table('tasks').insert(task_dict).execute()

                if result.data:
                    print(f"任务已添加到数据库: {task.global_task_id}")
                    return True
                else:
                    print(f"添加任务到数据库失败: {task.global_task_id}")
                    return False

        except Exception as e:
            print(f"添加任务时出错: {e}")
            return False

    def update_task(self, global_task_id: str, **kwargs) -> bool:
        """更新任务状态"""
        try:
            with self.lock:
                if global_task_id not in self.tasks:
                    return False

                task = self.tasks[global_task_id]

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

                result = self.supabase.table('tasks').update(update_data).eq('task_id', global_task_id).execute()

                if result.data:
                    logger.debug(f"Task updated successfully: {global_task_id}, affected rows: {len(result.data)}")
                    return True
                else:
                    logger.warning(f"Task update returned no data for task_id: {global_task_id}")
                    return False

        except Exception as e:
            print(f"更新任务时出错: {e}")
            return False

    def get_task(self, global_task_id: str) -> Optional[GlobalTask]:
        """获取指定任务"""
        with self.lock:
            return self.tasks.get(global_task_id)

    def get_all_tasks(self) -> List[GlobalTask]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())

    def get_running_tasks(self) -> List[GlobalTask]:
        """获取正在运行的任务"""
        with self.lock:
            return [task for task in self.tasks.values() if task.status == 'running']

    def create_task(self, task_id: str, session_id: str, user_id: str,
                   task_description: str, config: Dict) -> GlobalTask:
        """Create a new global task"""
        task = GlobalTask(
            task_id=task_id,
            session_id=session_id,
            user_id=user_id,
            task_description=task_description,
            status="running",
            created_at=datetime.now(),
            last_activity=datetime.now(),
            config=config
        )
        self.add_task(task)
        return task

    def update_task_status(self, task_id: str, status: str, error_message: str = None, result: str = None):
        """Update task status"""
        update_data = {'status': status, 'last_activity': datetime.now()}
        if error_message:
            update_data['error_message'] = error_message
        if result:
            update_data['result'] = result
        if status in ['completed', 'stopped', 'error']:
            update_data['end_time'] = datetime.now()

        return self.update_task(task_id, **update_data)

    def get_tasks_by_session(self, session_id: str) -> List[GlobalTask]:
        """Get tasks by session ID"""
        with self.lock:
            return [task for task in self.tasks.values() if task.session_id == session_id]

    def stop_task(self, task_id: str) -> bool:
        """Stop a task"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    return False

                # Update task status
                self.update_task_status(task_id, "stopped")

                # Stop thread if exists
                if task_id in self.active_threads:
                    try:
                        thread = self.active_threads[task_id]
                        # 由于Python线程不能直接强制停止，我们只能标记状态
                        # 在实际的任务执行中需要检查停止标志
                        print(f"标记任务停止: {task_id}")
                    except Exception as thread_error:
                        print(f"停止线程时出错: {thread_error}")
                    finally:
                        del self.active_threads[task_id]

                return True

        except Exception as e:
            print(f"停止任务时出错: {e}")
            return False

    def delete_task(self, global_task_id: str) -> bool:
        """删除任务"""
        try:
            with self.lock:
                if global_task_id not in self.tasks:
                    return False

                # 从内存中删除
                del self.tasks[global_task_id]

                # 从数据库中删除
                result = self.supabase.table('tasks').delete().eq('task_id', global_task_id).execute()

                if result.data:
                    print(f"任务已删除: {global_task_id}")
                    return True
                else:
                    print(f"删除任务失败: {global_task_id}")
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
                        self.tasks[task.global_task_id] = task
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

    def register_thread(self, global_task_id: str, thread: threading.Thread):
        """注册任务线程"""
        with self.lock:
            self.active_threads[global_task_id] = thread

    def unregister_thread(self, global_task_id: str):
        """取消注册任务线程"""
        with self.lock:
            if global_task_id in self.active_threads:
                del self.active_threads[global_task_id]

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
            # Get task info
            task_result = self.supabase.table('tasks')\
                .select('*')\
                .eq('task_id', task_id)\
                .single()\
                .execute()

            # Get steps
            steps_result = self.supabase.table('task_steps')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('step_number', desc=False)\
                .execute()

            # Get screenshots
            screenshots_result = self.supabase.table('step_screenshots')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('created_at', desc=False)\
                .execute()

            return {
                'task': task_result.data if task_result.data else None,
                'steps': steps_result.data if steps_result.data else [],
                'screenshots': screenshots_result.data if screenshots_result.data else []
            }

        except Exception as e:
            logger.error(f"Error getting step report data: {e}")
            return {
                'task': None,
                'steps': [],
                'screenshots': []
            }

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