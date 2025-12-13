#!/usr/bin/env python3
"""
Supabase 任务管理器
用于替换本地pickle文件存储，使用Supabase云数据库进行任务持久化
"""

import os
import json
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client

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
        """从字典创建对象，处理datetime反序列化"""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_activity'), str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        if data.get('end_time') and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)

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
                    result TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
                CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
                """

                # 这里需要通过Supabase的SQL编辑器手动创建表，或者使用Supabase Dashboard
                print("请通过Supabase Dashboard创建tasks表，SQL如下：")
                print(create_table_sql)

            except Exception as create_error:
                print(f"创建表时出错: {create_error}")

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

                # 添加更新时间
                update_data['updated_at'] = datetime.now().isoformat()

                result = self.supabase.table('tasks').update(update_data).eq('global_task_id', global_task_id).execute()

                if result.data:
                    print(f"任务已更新: {global_task_id}")
                    return True
                else:
                    print(f"更新任务失败: {global_task_id}")
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
                result = self.supabase.table('tasks').delete().eq('global_task_id', global_task_id).execute()

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
        """从数据库加载所有任务"""
        try:
            print("正在从Supabase加载任务...")

            # 从数据库获取所有任务
            result = self.supabase.table('tasks').select('*').order('created_at', desc=True).execute()

            if result.data:
                with self.lock:
                    self.tasks.clear()
                    for task_data in result.data:
                        task = GlobalTask.from_dict(task_data)
                        self.tasks[task.global_task_id] = task

                print(f"成功加载 {len(self.tasks)} 个任务")
                return True
            else:
                print("数据库中没有任务")
                return True

        except Exception as e:
            print(f"加载任务时出错: {e}")
            # 如果数据库连接失败，使用空的任务列表
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