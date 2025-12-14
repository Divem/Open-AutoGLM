#!/usr/bin/env python3
"""
脚本持久化管理器
用于管理自动化脚本的存储、检索和操作
"""

import os
import json
import hashlib
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from supabase import create_client, Client

# 从环境变量获取Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SECRET_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

@dataclass
class ScriptRecord:
    """脚本记录数据模型"""
    id: Optional[str] = None
    task_id: str = ""
    task_name: str = ""
    description: str = ""
    total_steps: int = 0
    success_rate: float = 0.0
    execution_time: float = 0.0
    device_id: Optional[str] = None
    model_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    script_data: Dict = None
    script_metadata: Dict = None
    script_version: str = "1.0"
    checksum: Optional[str] = None
    is_active: bool = True

    def __post_init__(self):
        """初始化后处理"""
        if self.script_data is None:
            self.script_data = {}
        if self.script_metadata is None:
            self.script_metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """转换为字典，处理datetime序列化"""
        data = asdict(self)
        # 处理datetime对象
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ScriptRecord':
        """从字典创建对象，处理datetime反序列化"""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    def calculate_checksum(self) -> str:
        """计算脚本数据的校验和"""
        # 使用script_data和script_metadata计算校验和
        data_to_hash = {
            'script_data': self.script_data,
            'script_metadata': self.script_metadata,
            'script_version': self.script_version
        }
        data_str = json.dumps(data_to_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def validate_data(self) -> Tuple[bool, List[str]]:
        """验证脚本数据的完整性"""
        errors = []

        # 检查必需字段
        if not self.task_id:
            errors.append("task_id不能为空")
        if not self.task_name:
            errors.append("task_name不能为空")
        if self.total_steps < 0:
            errors.append("total_steps不能为负数")
        if not 0 <= self.success_rate <= 100:
            errors.append("success_rate必须在0-100之间")
        if self.execution_time < 0:
            errors.append("execution_time不能为负数")

        # 检查脚本数据
        if not self.script_data:
            errors.append("script_data不能为空")

        # 验证校验和
        if self.checksum:
            calculated_checksum = self.calculate_checksum()
            if calculated_checksum != self.checksum:
                errors.append("数据校验和不匹配，可能被篡改")

        return len(errors) == 0, errors


class ScriptManager:
    """脚本持久化管理器"""

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase配置未找到，请检查环境变量SUPABASE_URL和SUPABASE_SECRET_KEY")

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.lock = threading.Lock()

    def save_script(self, script_record: ScriptRecord) -> Optional[str]:
        """保存脚本到数据库"""
        try:
            with self.lock:
                # 验证数据
                is_valid, errors = script_record.validate_data()
                if not is_valid:
                    print(f"脚本数据验证失败: {errors}")
                    return None

                # 计算校验和
                script_record.checksum = script_record.calculate_checksum()

                # 准备保存数据
                script_dict = script_record.to_dict()

                # 如果有ID，更新；否则创建
                if script_record.id:
                    # 更新现有记录
                    result = self.supabase.table('scripts').update(script_dict).eq('id', script_record.id).execute()
                    if result.data:
                        print(f"脚本已更新: {script_record.id}")
                        return script_record.id
                else:
                    # 创建新记录
                    script_dict['id'] = str(uuid.uuid4())
                    result = self.supabase.table('scripts').insert(script_dict).execute()
                    if result.data:
                        script_id = result.data[0]['id']
                        script_record.id = script_id
                        print(f"脚本已创建: {script_id}")
                        return script_id

                print(f"保存脚本失败: {script_record.task_id}")
                return None

        except Exception as e:
            print(f"保存脚本时出错: {e}")
            return None

    def get_script(self, script_id: str) -> Optional[ScriptRecord]:
        """获取指定脚本"""
        try:
            result = self.supabase.table('scripts').select('*').eq('id', script_id).execute()
            if result.data:
                script_data = result.data[0]
                return ScriptRecord.from_dict(script_data)
            return None
        except Exception as e:
            print(f"获取脚本时出错: {e}")
            return None

    def get_scripts_by_task_id(self, task_id: str) -> List[ScriptRecord]:
        """根据任务ID获取脚本"""
        try:
            result = self.supabase.table('scripts').select('*').eq('task_id', task_id).eq('is_active', True).execute()
            if result.data:
                return [ScriptRecord.from_dict(script_data) for script_data in result.data]
            return []
        except Exception as e:
            print(f"根据任务ID获取脚本时出错: {e}")
            return []

    def search_scripts(self, keyword: str = "", device_id: str = "",
                      model_name: str = "", limit: int = 50, offset: int = 0) -> List[ScriptRecord]:
        """搜索脚本"""
        try:
            query = self.supabase.table('scripts').select('*').eq('is_active', True)

            if keyword:
                query = query.or_(f"task_name.ilike.%{keyword}%,description.ilike.%{keyword}%")
            if device_id:
                query = query.eq('device_id', device_id)
            if model_name:
                query = query.eq('model_name', model_name)

            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            result = query.execute()

            if result.data:
                return [ScriptRecord.from_dict(script_data) for script_data in result.data]
            return []
        except Exception as e:
            print(f"搜索脚本时出错: {e}")
            return []

    def get_script_summary(self, limit: int = 100) -> List[Dict]:
        """获取脚本摘要信息"""
        try:
            result = self.supabase.table('script_summary').select('*').order('created_at', desc=True).limit(limit).execute()
            if result.data:
                return result.data
            return []
        except Exception as e:
            print(f"获取脚本摘要时出错: {e}")
            return []

    def delete_script(self, script_id: str, soft_delete: bool = True) -> bool:
        """删除脚本"""
        try:
            with self.lock:
                if soft_delete:
                    # 软删除：标记为非活跃状态
                    result = self.supabase.table('scripts').update({'is_active': False}).eq('id', script_id).execute()
                else:
                    # 硬删除
                    result = self.supabase.table('scripts').delete().eq('id', script_id).execute()

                if result.data:
                    print(f"脚本已删除: {script_id}")
                    return True
                else:
                    print(f"删除脚本失败: {script_id}")
                    return False
        except Exception as e:
            print(f"删除脚本时出错: {e}")
            return False

    def export_script(self, script_id: str, format: str = "json") -> Optional[str]:
        """导出脚本"""
        try:
            script = self.get_script(script_id)
            if not script:
                return None

            if format.lower() == "json":
                return json.dumps(script.to_dict(), ensure_ascii=False, indent=2)
            elif format.lower() == "python":
                # 生成Python重放脚本
                return self._generate_python_replay_script(script)
            else:
                print(f"不支持的导出格式: {format}")
                return None
        except Exception as e:
            print(f"导出脚本时出错: {e}")
            return None

    def _generate_python_replay_script(self, script: ScriptRecord) -> str:
        """生成Python重放脚本"""
        script_data = script.script_data
        metadata = script.script_metadata

        python_code = f'''#!/usr/bin/env python3
"""
Auto-generated replay script for Terminal Agent task.
Generated on: {datetime.now().isoformat()}
Task: {script.task_name}
Description: {script.description}
Total Steps: {script.total_steps}
Success Rate: {script.success_rate}%

To run this script:
    python replay_script.py

Requirements:
    - phone_agent package
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
    """Replay script for Terminal Agent automation."""

    def __init__(self, script_data: dict, metadata: dict):
        """
        Initialize the replay script.

        Args:
            script_data: Dictionary containing the script steps and data
            metadata: Dictionary containing script metadata
        """
        self.script_data = script_data
        self.metadata = metadata
        self.steps = script_data.get("steps", [])

    def print_info(self):
        """Print script information."""
        print("=" * 60)
        print("📱 Terminal Agent Replay Script")
        print("=" * 60)
        task_name = self.metadata.get('task_name', 'Unknown')
        description = self.metadata.get('description', 'No description')
        total_steps = self.metadata.get('total_steps', 0)
        success_rate = self.metadata.get('success_rate', 0)
        execution_time = self.metadata.get('execution_time')

        print(f"Task: {{task_name}}")
        print(f"Description: {{description}}")
        print(f"Total Steps: {{total_steps}}")
        print(f"Success Rate: {{success_rate}}%")
        if execution_time:
            print(f"Original Execution Time: {{execution_time}}s")
        print("=" * 60)

    def replay(self, device_id: str = None, delay: float = 1.0):
        """
        Replay the recorded actions.

        Args:
            device_id: Optional device ID
            delay: Delay between actions in seconds
        """
        self.print_info()

        print("\\n🚀 Starting replay...")
        print(f"⚡ Delay between actions: {{delay}}s")
        device_display = device_id or 'default'
        print(f"📱 Device ID: {{device_display}}")

        input("\\nPress Enter to start, or Ctrl+C to cancel...")

        successful_steps = 0

        try:
            for i, step in enumerate(self.steps, 1):
                action_type = step.get('action_type', 'Unknown')
                total_steps_len = len(self.steps)
                print(f"\\n--- Step {{i}}/{{total_steps_len}}: {{action_type}} ---")

                if not step.get('success', True):
                    error_msg = step.get('error_message', 'Unknown error')
                    print(f"⚠️  Skipping failed step: {{error_msg}}")
                    continue

                action_data = step.get('action_data', {{}})
                action_name = action_data.get('action')

                if action_name == 'Launch':
                    app_name = action_data.get('app')
                    if app_name:
                        print(f"🔧 Launching app: {{app_name}}")
                        launch_app(app_name, device_id)

                elif action_name == 'Tap':
                    element = action_data.get('element')
                    if element and len(element) >= 2:
                        x, y = element[0], element[1]
                        print(f"🔧 Tapping at relative coordinates: ({{x}}, {{y}})")
                        # Note: You'll need to implement coordinate conversion for actual tapping
                        # tap(x, y, device_id)

                elif action_name == 'Type':
                    text = action_data.get('text', '')
                    if text:
                        display_text = text[:50] + ('...' if len(text) > 50 else '')
                        print(f"🔧 Typing text: {{display_text}}")
                        # Note: You'll need to implement keyboard switching for actual typing
                        # type_text(text, device_id)

                elif action_name == 'Swipe':
                    start = action_data.get('start')
                    end = action_data.get('end')
                    if start and end and len(start) >= 2 and len(end) >= 2:
                        print(f"🔧 Swiping from {{start}} to {{end}}")
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
                        print(f"🔧 Waiting {{wait_time}}s")
                        time.sleep(wait_time)
                    except ValueError:
                        print(f"🔧 Waiting 1s (default)")
                        time.sleep(1.0)

                else:
                    print(f"⚠️  Unknown action: {{action_name}}")

                successful_steps += 1

                # Wait between actions
                if delay > 0 and i < len(self.steps):
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\\n⚡ Replay interrupted by user")
            return

        print("\\n" + "=" * 60)
        print(f"✅ Replay completed: {{successful_steps}}/{{len(self.steps)}} steps")
        print("=" * 60)


def main():
    """Main function to run the replay script."""
    if len(sys.argv) != 2:
        print("Usage: python replay_script.py <script_data.json>")
        sys.exit(1)

    json_file = sys.argv[1]

    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: Script file not found: {{json_file}}")
        sys.exit(1)

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in script file: {{e}}")
        sys.exit(1)

    metadata = script_data.get("metadata", {{}})

    replay = ReplayScript(script_data, metadata)

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
'''
        return python_code

    def cleanup_old_scripts(self, days: int = 90) -> int:
        """清理旧脚本"""
        try:
            cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)

            result = self.supabase.table('scripts').update({'is_active': False}).lt('created_at', cutoff_date.isoformat()).execute()

            if result.data:
                cleaned_count = len(result.data)
                print(f"清理了 {cleaned_count} 个旧脚本")
                return cleaned_count
            else:
                print("没有需要清理的旧脚本")
                return 0
        except Exception as e:
            print(f"清理旧脚本时出错: {e}")
            return 0


# 导出主要类
__all__ = ['ScriptManager', 'ScriptRecord']