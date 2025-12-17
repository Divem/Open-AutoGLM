#!/usr/bin/env python3
"""
Phone Agent Web Interface
Web interface for Phone Agent with multi-turn conversation support
"""

import os
import sys
import json
import asyncio
import threading
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from flask import Flask, render_template, request, jsonify, session, send_from_directory, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in parent directory
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 已加载环境变量: {env_path}")
    else:
        print(f"⚠️  未找到.env文件: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法自动加载.env文件")
except Exception as e:
    print(f"⚠️  加载环境变量时出错: {e}")

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig
from phone_agent.recorder import ScriptRecorder
from phone_agent.stop_handler import StopException, StopReason

# Initialize logger early
import logging
logger = logging.getLogger(__name__)

# 导入脚本管理器
try:
    from web.supabase_manager import SupabaseTaskManager, GlobalTask
    SUPABASE_AVAILABLE = True
    logger.info("✅ Supabase manager imported successfully")
except ImportError as e:
    SUPABASE_AVAILABLE = False
    logger.error(f"❌ Failed to import Supabase manager: {e}")
    # 回退到本地GlobalTask定义
    @dataclass
    class GlobalTask:
        task_id: str
        session_id: str
        user_id: str
        task_description: str
        status: str
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
            return self.task_id

try:
    from script_manager import ScriptManager
    SCRIPT_MANAGER_AVAILABLE = True
except ImportError:
    SCRIPT_MANAGER_AVAILABLE = False


# Helper functions for step tracking
def calculate_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hash as a hex string
    """
    import hashlib
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {e}")
        return ""


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


class PhoneAgentWeb:

    def __init__(self, storage_file: str = "web_tasks.pkl"):
        self.storage_file = Path(__file__).parent / storage_file
        self.tasks: Dict[str, GlobalTask] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.load_tasks()

    def load_tasks(self):
        """Load tasks from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'rb') as f:
                    self.tasks = pickle.load(f)
                print(f"Loaded {len(self.tasks)} tasks from storage")
            except Exception as e:
                print(f"Failed to load tasks: {e}")
                self.tasks = {}

    def save_tasks(self):
        """Save tasks to storage"""
        try:
            with open(self.storage_file, 'wb') as f:
                pickle.dump(self.tasks, f)
        except Exception as e:
            print(f"Failed to save tasks: {e}")

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
        self.tasks[task_id] = task
        self.save_tasks()
        return task

    def update_task_status(self, task_id: str, status: str, error_message: str = None):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].last_activity = datetime.now()
            if error_message:
                self.tasks[task_id].error_message = error_message
            self.save_tasks()

    def get_task(self, task_id: str) -> Optional[GlobalTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[GlobalTask]:
        """Get all tasks"""
        return list(self.tasks.values())

    def get_tasks_by_session(self, session_id: str) -> List[GlobalTask]:
        """Get tasks by session ID"""
        return [task for task in self.tasks.values() if task.session_id == session_id]

    def register_thread(self, task_id: str, thread: threading.Thread):
        """Register a thread for a task"""
        self.active_threads[task_id] = thread

    def stop_task(self, task_id: str) -> bool:
        """Stop a task"""
        if task_id in self.active_threads:
            try:
                # Update task status
                self.update_task_status(task_id, "stopped")
                # The thread will check this status and stop
                return True
            except Exception as e:
                print(f"Failed to stop task {task_id}: {e}")
                return False
        return False

    def cleanup_old_tasks(self, hours: int = 24):
        """Clean up old tasks"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        old_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.created_at.timestamp() < cutoff_time and task.status in ["completed", "error", "stopped"]
        ]
        for task_id in old_tasks:
            del self.tasks[task_id]
        if old_tasks:
            self.save_tasks()
            print(f"Cleaned up {len(old_tasks)} old tasks")


# Global task manager instance - 使用Supabase
global_task_manager = None
try:
    from supabase_manager import SupabaseTaskManager
    global_task_manager = SupabaseTaskManager()
    print("✅ Supabase任务管理器初始化成功")
except Exception as e:
    print(f"❌ Supabase任务管理器初始化失败: {e}")
    print("回退到本地存储...")
    global_task_manager = None

# 创建本地Web任务管理器作为回退
web_task_manager = PhoneAgentWeb()


@dataclass
class TaskSession:
    """Task session information"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    agent: Optional[PhoneAgent] = None
    current_task: Optional[str] = None
    task_status: str = "idle"  # idle, running, completed, error
    conversation_history: List[Dict] = None
    screenshots: List[str] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.screenshots is None:
            self.screenshots = []


class PhoneAgentWeb:
    """Phone Agent Web Interface"""

    def __init__(self, host='0.0.0.0', port=5000, debug=False):
        self.host = host
        self.port = port
        self.debug = debug

        # Create Flask app
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)

        # Configure upload folders
        self.app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'static' / 'uploads'
        self.app.config['SCREENSHOTS_FOLDER'] = Path(__file__).parent / 'static' / 'screenshots'
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

        # Create directories
        self.app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
        self.app.config['SCREENSHOTS_FOLDER'].mkdir(exist_ok=True)

        # Initialize SocketIO with more robust configuration
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            ping_timeout=5000,
            ping_interval=25000,
            engineio_logger=True
        )

        # Storage
        self.sessions: Dict[str, TaskSession] = {}
        self.agent_configs: Dict[str, Any] = {
            'default': {
                'base_url': os.getenv('PHONE_AGENT_BASE_URL', 'http://localhost:8000/v1'),
                'model_name': os.getenv('PHONE_AGENT_MODEL', 'autoglm-phone-9b'),
                'api_key': os.getenv('PHONE_AGENT_API_KEY', 'EMPTY'),
                'max_steps': 100,
                'device_id': None,
                'lang': 'cn',
                'verbose': True,
                'record_script': True,
                'script_output_dir': 'web_scripts'
            }
        }

        # Setup logger
        self.logger = logging.getLogger(__name__)

        # Setup custom template filters
        self.setup_template_filters()

        # Setup routes
        self.setup_routes()
        self.setup_socketio()

    def setup_template_filters(self):
        """Setup custom Jinja2 template filters"""

        @self.app.template_filter('datetimeformat')
        def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
            """Format datetime value"""
            if value is None:
                return ""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    return value
            return value.strftime(format)

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.after_request
        def add_header(response):
            """Add headers to disable caching for development"""
            # 禁用浏览器缓存，确保使用最新的JavaScript代码
            if 'Cache-Control' not in response.headers:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            if 'Pragma' not in response.headers:
                response.headers['Pragma'] = 'no-cache'
            if 'Expires' not in response.headers:
                response.headers['Expires'] = '0'
            return response

        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')

        @self.app.route('/config')
        def config():
            """Configuration page"""
            return render_template('config.html')

        @self.app.route('/api/sessions', methods=['POST'])
        def create_session():
            """Create new session"""
            session_id = str(uuid.uuid4())
            user_id = request.json.get('user_id', 'anonymous')

            # Create session
            task_session = TaskSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )

            self.sessions[session_id] = task_session

            return jsonify({
                'session_id': session_id,
                'created_at': task_session.created_at.isoformat()
            })

        @self.app.route('/api/sessions/<session_id>', methods=['GET'])
        def get_session(session_id):
            """Get session information"""
            if session_id not in self.sessions:
                return jsonify({'error': 'Session not found'}), 404

            session_data = self.sessions[session_id]
            return jsonify({
                'session_id': session_data.session_id,
                'user_id': session_data.user_id,
                'created_at': session_data.created_at.isoformat(),
                'last_activity': session_data.last_activity.isoformat(),
                'current_task': session_data.current_task,
                'task_status': session_data.task_status,
                'conversation_count': len(session_data.conversation_history)
            })

        @self.app.route('/api/config', methods=['GET', 'POST'])
        def handle_config():
            """Get or update configuration"""
            if request.method == 'GET':
                return jsonify(self.agent_configs)

            # Update configuration
            config_data = request.json
            config_name = config_data.get('name', 'default')

            self.agent_configs[config_name] = config_data

            return jsonify({'message': 'Configuration updated'})

        @self.app.route('/api/devices', methods=['GET'])
        def list_devices():
            """List available devices"""
            try:
                from phone_agent.adb import list_devices
                devices = list_devices()
                return jsonify([{
                    'device_id': d.device_id,
                    'connection_type': d.connection_type.value,
                    'model': getattr(d, 'model', 'Unknown')
                } for d in devices])
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/apps', methods=['GET'])
        def list_apps():
            """List supported apps"""
            try:
                from phone_agent.config.apps import APP_PACKAGES
                return jsonify(list(APP_PACKAGES.keys()))
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/screenshots/<path:filename>')
        def serve_screenshot(filename):
            """Serve screenshot files with Supabase fallback"""
            # First try local file
            local_path = os.path.join(self.app.config['SCREENSHOTS_FOLDER'], filename)
            if os.path.exists(local_path):
                return send_from_directory(self.app.config['SCREENSHOTS_FOLDER'], filename)

            # If not found locally, try to fetch from Supabase Storage
            # This would require additional implementation
            from flask import abort
            abort(404, description="Screenshot not found locally and Supabase fallback not implemented")

        @self.app.route('/uploads/<path:filename>')
        def serve_upload(filename):
            """Serve uploaded files"""
            return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename)

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查端点"""
            try:
                # 检查数据库连接
                task_count = len(global_task_manager.get_all_tasks())

                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat() + 'Z',
                    'service': 'phone-agent-web',
                    'database': {
                        'status': 'connected',
                        'task_count': task_count
                    }
                })
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat() + 'Z'
                }), 500

        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get all tasks"""
            try:
                logger.info(f"API请求: 获取任务列表, 参数: {dict(request.args)}")

                session_id = request.args.get('session_id')
                if session_id:
                    logger.info(f"按会话ID过滤: {session_id}")
                    tasks = global_task_manager.get_tasks_by_session(session_id)
                else:
                    logger.info("获取所有任务")
                    tasks = global_task_manager.get_all_tasks()

                logger.info(f"获取到 {len(tasks)} 个任务")

                task_list = []
                for i, task in enumerate(tasks):
                    try:
                        task_data = {
                            'task_id': task.task_id,
                            'session_id': task.session_id,
                            'user_id': task.user_id,
                            'task_description': task.task_description,
                            'status': task.status,
                            'start_time': task.created_at.isoformat() + 'Z',  # 确保UTC时间有Z后缀
                            'end_time': task.end_time.isoformat() + 'Z' if task.end_time else None,
                            'last_activity': task.last_activity.isoformat() + 'Z',
                            'error_message': task.error_message,
                            'result': task.result
                        }
                        task_list.append(task_data)

                        if i < 3:  # 记录前3个任务详情
                            logger.debug(f"任务样本 {i+1}: {task.task_id} - {task.status} - {task.task_description}")

                    except Exception as task_error:
                        logger.error(f"处理任务 {task.task_id} 时出错: {task_error}")
                        # 继续处理其他任务
                        continue

                response_data = {
                    'data': {
                        'tasks': task_list,
                        'total': len(task_list),
                        'timestamp': datetime.now().isoformat() + 'Z'
                    }
                }

                logger.info(f"成功返回 {len(task_list)} 个任务数据")
                return jsonify(response_data)

            except Exception as e:
                logger.error(f"获取任务列表失败: {e}", exc_info=True)
                error_response = {
                    'error': f'Failed to fetch tasks: {str(e)}',
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
                return jsonify(error_response), 500

        @self.app.route('/api/tasks/<task_id>/stop', methods=['POST'])
        def stop_task(task_id):
            """Stop a running task"""
            success = global_task_manager.stop_task(task_id)
            if success:
                return jsonify({'message': 'Task stopped successfully'})
            else:
                return jsonify({'error': 'Task not found or cannot be stopped'}), 404

        # Step tracking API endpoints
        @self.app.route('/api/tasks/<task_id>/steps', methods=['GET'])
        def get_task_steps(task_id):
            """Get all steps for a task"""
            try:
                limit = request.args.get('limit', type=int)
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 20, type=int), 100)

                # Get steps from database
                steps = global_task_manager.get_task_steps(task_id, limit)

                # Pagination
                total_steps = len(steps)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_steps = steps[start_idx:end_idx]

                return jsonify({
                    'data': {
                        'steps': paginated_steps,
                        'pagination': {
                            'page': page,
                            'per_page': per_page,
                            'total': total_steps,
                            'pages': (total_steps + per_page - 1) // per_page
                        }
                    }
                })
            except Exception as e:
                return jsonify({'error': f'Failed to get task steps: {str(e)}'}), 500

        @self.app.route('/api/tasks/<task_id>/report', methods=['GET'])
        def get_task_report(task_id):
            """Generate task execution report"""
            try:
                # Get report data
                report_data = global_task_manager.get_step_report_data(task_id)

                if not report_data['task']:
                    return jsonify({'error': 'Task not found'}), 404

                # Calculate statistics
                steps = report_data['steps']
                total_steps = len(steps)
                successful_steps = len([s for s in steps if s.get('success') is True])
                failed_steps = total_steps - successful_steps
                total_duration = sum(s.get('duration_ms') or 0 for s in steps)

                report = {
                    'task': report_data['task'],
                    'steps': steps,
                    'screenshots': report_data['screenshots'],
                    'statistics': {
                        'total_steps': total_steps,
                        'successful_steps': successful_steps,
                        'failed_steps': failed_steps,
                        'success_rate': successful_steps / max(total_steps, 1),
                        'total_duration_ms': total_duration,
                        'average_step_duration_ms': total_duration / max(total_steps, 1),
                        'screenshots_count': len(report_data['screenshots'])
                    }
                }

                return jsonify({'data': report})
            except Exception as e:
                return jsonify({'error': f'Failed to generate task report: {str(e)}'}), 500

        @self.app.route('/api/tasks/<task_id>/screenshots', methods=['GET'])
        def get_task_screenshots(task_id):
            """Get all screenshots for a task"""
            try:
                screenshots = global_task_manager.get_step_screenshots(task_id)

                # Group screenshots by step
                screenshots_by_step = {}
                for screenshot in screenshots:
                    step_id = screenshot.get('step_id')
                    if step_id not in screenshots_by_step:
                        screenshots_by_step[step_id] = []
                    screenshots_by_step[step_id].append(screenshot)

                return jsonify({
                    'data': {
                        'screenshots': screenshots,
                        'grouped_by_step': screenshots_by_step,
                        'total_count': len(screenshots)
                    }
                })
            except Exception as e:
                return jsonify({'error': f'Failed to get task screenshots: {str(e)}'}), 500

        # Task report page
        @self.app.route('/tasks/<task_id>/report')
        def task_report_page(task_id):
            """Render task report page"""
            try:
                # Get task basic info
                task = global_task_manager.get_task(task_id)
                if not task:
                    return render_template('404.html'), 404

                return render_template('task_report.html', task=task)
            except Exception as e:
                logger.error(f"Error rendering task report page: {e}")
                return render_template('error.html', error=str(e)), 500

        # Statistics API endpoints
        @self.app.route('/api/statistics', methods=['GET'])
        def get_statistics():
            """Get overall statistics"""
            try:
                # Get days parameter (default: 30)
                days = request.args.get('days', 30, type=int)

                # Get statistics from SupabaseTaskManager
                if hasattr(global_task_manager, 'get_statistics'):
                    stats = global_task_manager.get_statistics()
                    return jsonify(stats)
                else:
                    return jsonify({'error': 'Statistics not available'}), 503

            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/tasks/summary', methods=['GET'])
        def get_task_summary():
            """Get task summary for dashboard"""
            try:
                # Get days parameter (default: 30)
                days = request.args.get('days', 30, type=int)

                # Try to get detailed summary first
                if hasattr(global_task_manager, 'get_task_summary'):
                    summary = global_task_manager.get_task_summary(days)
                else:
                    # Fallback to basic statistics
                    if hasattr(global_task_manager, 'get_statistics'):
                        stats = global_task_manager.get_statistics()
                        summary = {
                            'total_tasks': stats['tasks']['total'],
                            'completed_tasks': stats['tasks']['completed'],
                            'failed_tasks': stats['tasks']['failed'],
                            'success_rate': 0,
                            'daily_stats': [],
                            'period_days': days
                        }
                        if stats['tasks']['total'] > 0:
                            summary['success_rate'] = round(
                                (stats['tasks']['completed'] / stats['tasks']['total']) * 100, 2
                            )
                    else:
                        summary = {
                            'total_tasks': 0,
                            'completed_tasks': 0,
                            'failed_tasks': 0,
                            'success_rate': 0,
                            'daily_stats': [],
                            'period_days': days
                        }

                return jsonify(summary)

            except Exception as e:
                logger.error(f"Error getting task summary: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/tasks/<task_id>', methods=['GET'])
        def get_task(task_id):
            """Get task by ID"""
            try:
                task = global_task_manager.get_task(task_id)
                if task:
                    return jsonify({
                        'data': {
                            'task': {
                                'task_id': task.task_id,
                                'session_id': task.session_id,
                                'user_id': task.user_id,
                                'task_description': task.task_description,
                                'status': task.status,
                                'start_time': task.created_at.isoformat(),  # 映射为前端期望的字段名
                                'end_time': task.end_time.isoformat() if task.end_time else None,
                                'last_activity': task.last_activity.isoformat(),
                                'error_message': task.error_message,
                                'result': task.result,
                                'config': task.config
                            }
                        }
                    })
                else:
                    return jsonify({'error': 'Task not found'}), 404
            except Exception as e:
                return jsonify({'error': f'Failed to fetch task: {str(e)}'}), 500

        # Script management APIs
        @self.app.route('/api/scripts', methods=['GET'])
        def get_scripts():
            """Get scripts with optional search and filtering"""
            try:
                if not SCRIPT_MANAGER_AVAILABLE:
                    return jsonify({'error': 'Script management not available'}), 503

                # Initialize script manager
                script_manager = ScriptManager()

                # Get query parameters
                keyword = request.args.get('keyword', '')
                device_id = request.args.get('device_id', '')
                model_name = request.args.get('model_name', '')
                limit = int(request.args.get('limit', 50))
                offset = int(request.args.get('offset', 0))

                # Search scripts
                scripts = script_manager.search_scripts(
                    keyword=keyword,
                    device_id=device_id,
                    model_name=model_name,
                    limit=limit,
                    offset=offset
                )

                # Convert to response format
                script_list = []
                for script in scripts:
                    script_list.append({
                        'id': script.id,
                        'task_name': script.task_name,
                        'description': script.description,
                        'total_steps': script.total_steps,
                        'success_rate': script.success_rate,
                        'execution_time': script.execution_time,
                        'device_id': script.device_id,
                        'model_name': script.model_name,
                        'created_at': script.created_at.isoformat() if script.created_at else None
                    })

                return jsonify({'data': {'scripts': script_list}})
            except Exception as e:
                return jsonify({'error': f'Failed to fetch scripts: {str(e)}'}), 500

        @self.app.route('/api/scripts/<script_id>', methods=['GET'])
        def get_script(script_id):
            """Get script details by ID"""
            try:
                script_manager = ScriptManager()
                script = script_manager.get_script(script_id)

                if script:
                    return jsonify({'data': script.to_dict()})
                else:
                    return jsonify({'error': 'Script not found'}), 404
            except Exception as e:
                return jsonify({'error': f'Failed to fetch script: {str(e)}'}), 500

        @self.app.route('/api/scripts/<script_id>/export', methods=['GET'])
        def export_script(script_id):
            """Export script in specified format"""
            try:
                script_manager = ScriptManager()
                format_type = request.args.get('format', 'json').lower()

                if format_type not in ['json', 'python']:
                    return jsonify({'error': 'Invalid format. Supported formats: json, python'}), 400

                script_content = script_manager.export_script(script_id, format_type)

                if script_content is None:
                    return jsonify({'error': 'Script not found'}), 404

                if format_type == 'json':
                    return Response(
                        script_content,
                        mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename=script_{script_id}.json'}
                    )
                else:  # python
                    return Response(
                        script_content,
                        mimetype='text/x-python',
                        headers={'Content-Disposition': f'attachment; filename=replay_script_{script_id}.py'}
                    )
            except Exception as e:
                return jsonify({'error': f'Failed to export script: {str(e)}'}), 500

        @self.app.route('/api/scripts/<script_id>/replay', methods=['POST'])
        def replay_script(script_id):
            """Initiate script replay"""
            try:
                script_manager = ScriptManager()
                script = script_manager.get_script(script_id)

                if not script:
                    return jsonify({'error': 'Script not found'}), 404

                # Get replay parameters
                device_id = request.json.get('device_id')
                delay = float(request.json.get('delay', 1.0))

                # For now, return the script data for client-side replay
                # In future, this could trigger server-side replay
                return jsonify({
                    'message': 'Script replay initiated',
                    'script_id': script_id,
                    'script_data': script.to_dict(),
                    'replay_params': {
                        'device_id': device_id,
                        'delay': delay
                    }
                })
            except Exception as e:
                return jsonify({'error': f'Failed to initiate script replay: {str(e)}'}), 500

        @self.app.route('/api/scripts/<script_id>', methods=['DELETE'])
        def delete_script(script_id):
            """Delete script (soft delete)"""
            try:
                script_manager = ScriptManager()
                success = script_manager.delete_script(script_id, soft_delete=True)

                if success:
                    return jsonify({'message': 'Script deleted successfully'})
                else:
                    return jsonify({'error': 'Script not found'}), 404
            except Exception as e:
                return jsonify({'error': f'Failed to delete script: {str(e)}'}), 500

        @self.app.route('/api/scripts/summary', methods=['GET'])
        def get_script_summary():
            """Get script summary statistics"""
            try:
                script_manager = ScriptManager()
                limit = int(request.args.get('limit', 100))
                summary = script_manager.get_script_summary(limit=limit)

                return jsonify({'data': {'summary': summary}})
            except Exception as e:
                return jsonify({'error': f'Failed to fetch script summary: {str(e)}'}), 500

        # Screenshot fallback configuration APIs
        @self.app.route('/api/config/screenshot-fallback', methods=['GET'])
        def get_screenshot_fallback_config():
            """Get screenshot fallback configuration"""
            try:
                from supabase_manager import LocalFileScanner
                scanner = LocalFileScanner()

                config_data = {
                    'config': scanner.config,
                    'performance_stats': scanner.get_performance_stats() if scanner.config['enable_performance_monitoring'] else None,
                    'is_enabled': scanner.is_enabled()
                }

                return jsonify({'data': config_data})
            except Exception as e:
                return jsonify({'error': f'Failed to get screenshot fallback config: {str(e)}'}), 500

        @self.app.route('/api/config/screenshot-fallback', methods=['POST'])
        def update_screenshot_fallback_config():
            """Update screenshot fallback configuration"""
            try:
                from supabase_manager import LocalFileScanner
                scanner = LocalFileScanner()

                new_config = request.json.get('config', {})
                if not isinstance(new_config, dict):
                    return jsonify({'error': 'Invalid config format'}), 400

                # Validate configuration values
                valid_keys = scanner.config.keys()
                for key, value in new_config.items():
                    if key not in valid_keys:
                        return jsonify({'error': f'Invalid config key: {key}'}), 400

                # Update configuration
                scanner.update_config(new_config)

                return jsonify({'message': 'Configuration updated successfully', 'config': scanner.config})
            except Exception as e:
                return jsonify({'error': f'Failed to update screenshot fallback config: {str(e)}'}), 500

        @self.app.route('/api/config/screenshot-fallback/clear-cache', methods=['POST'])
        def clear_screenshot_cache():
            """Clear screenshot scan cache"""
            try:
                from supabase_manager import LocalFileScanner
                scanner = LocalFileScanner()
                scanner.clear_cache()

                return jsonify({'message': 'Screenshot cache cleared successfully'})
            except Exception as e:
                return jsonify({'error': f'Failed to clear screenshot cache: {str(e)}'}), 500

        @self.app.route('/api/config/screenshot-fallback/test', methods=['POST'])
        def test_screenshot_fallback():
            """Test screenshot fallback functionality"""
            try:
                from supabase_manager import LocalFileScanner, SupabaseManager
                import time

                test_start_time = time.time()
                scanner = LocalFileScanner()

                # Test if scanner is enabled
                if not scanner.is_enabled():
                    return jsonify({
                        'success': False,
                        'message': 'Screenshot fallback is disabled',
                        'config': scanner.config
                    })

                # Test file scanning
                local_files = scanner.scan_screenshots()
                scan_time = time.time() - test_start_time

                # Get performance stats
                perf_stats = scanner.get_performance_stats()

                test_result = {
                    'success': True,
                    'message': 'Screenshot fallback test completed',
                    'config': scanner.config,
                    'scan_results': {
                        'files_found': len(local_files),
                        'scan_time': scan_time,
                        'first_file': local_files[0].name if local_files else None
                    },
                    'performance_stats': perf_stats,
                    'cache_info': {
                        'cache_valid': perf_stats.get('cache_valid', False),
                        'cached_files': perf_stats.get('cached_files_count', 0)
                    }
                }

                return jsonify({'data': test_result})
            except Exception as e:
                return jsonify({'error': f'Screenshot fallback test failed: {str(e)}'}), 500

        
    def setup_socketio(self):
        """Setup SocketIO handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            print(f"Client connected: {request.sid}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print(f"Client disconnected: {request.sid}")

        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Join a session room"""
            session_id = data.get('session_id')
            if session_id:
                join_room(session_id)
                emit('joined_session', {'session_id': session_id})

        @self.socketio.on('send_task')
        def handle_send_task(data):
            """Handle task execution request"""
            session_id = data.get('session_id')
            task_description = data.get('task')
            config = data.get('config', {})

            if not session_id or not task_description:
                emit('error', {'message': 'Missing session_id or task'})
                return

            if session_id not in self.sessions:
                emit('error', {'message': 'Invalid session_id'})
                return

            # Execute task asynchronously
            thread = threading.Thread(
                target=self._execute_task_thread,
                args=(session_id, task_description, config, request.sid)
            )
            thread.daemon = True
            thread.start()

        @self.socketio.on('stop_task')
        def handle_stop_task(data):
            """Handle task stop request"""
            session_id = data.get('session_id')

            if session_id in self.sessions:
                session_data = self.sessions[session_id]

                # Update session status
                session_data.task_status = 'stopped'

                # Stop the agent directly if available
                if hasattr(session_data, 'agent') and session_data.agent:
                    try:
                        logger.info(f"🛑 Stopping agent for session {session_id}")
                        session_data.agent.stop(
                            reason="User requested stop",
                            message="Task stopped by user via web interface"
                        )
                    except Exception as e:
                        logger.error(f"Error stopping agent: {e}")
                        import traceback
                        traceback.print_exc()

                # Update database task status if task_id exists
                if hasattr(session_data, 'task_id') and session_data.task_id:
                    try:
                        global_task_manager.update_task_status(session_data.task_id, 'stopped')
                    except Exception as e:
                        logger.error(f"Error updating task status in database: {e}")

                emit('task_stopped', {
                    'session_id': session_id,
                    'message': 'Task stopped by user'
                }, room=session_id)

    def _execute_task_thread(self, session_id: str, task_description: str, config: Dict, client_sid: str):
        """Execute task in separate thread"""
        # Generate unique task ID
        task_id = str(uuid.uuid4())

        try:
            session_data = self.sessions[session_id]

            # Create global task
            global_task = global_task_manager.create_task(
                task_id=task_id,
                session_id=session_id,
                user_id='web_user',
                task_description=task_description,
                config=config
            )

            # Update session
            session_data.current_task = task_description
            session_data.last_activity = datetime.now()
            session_data.task_id = task_id  # Store task ID in session

            # Create agent config
            agent_config = self._create_agent_config(config)

            # Create agent
            model_config = ModelConfig(
                base_url=agent_config.get('base_url', 'http://localhost:8000/v1'),
                api_key=agent_config.get('api_key', 'EMPTY'),
                model_name=agent_config.get('model_name', 'autoglm-phone-9b')
            )

            agent_config_obj = AgentConfig(
                max_steps=agent_config.get('max_steps', 100),
                device_id=agent_config.get('device_id'),
                lang=agent_config.get('lang', 'cn'),
                verbose=agent_config.get('verbose', True),
                record_script=agent_config.get('record_script', False),
                script_output_dir=agent_config.get('script_output_dir', 'web_scripts')
            )

            # Create agent with callbacks
            agent = PhoneAgent(
                model_config=model_config,
                agent_config=agent_config_obj,
                task_id=task_id
            )

            session_data.agent = agent
            session_data.task_status = 'running'

            # Notify start
            self.socketio.emit('task_started', {
                'session_id': session_id,
                'task': task_description,
                'task_id': task_id,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)

            # Add to conversation history
            session_data.conversation_history.append({
                'role': 'user',
                'content': task_description,
                'timestamp': datetime.now().isoformat()
            })

            # Custom step callback for real-time updates
            def step_callback(step_data):
                """Callback for each step"""
                # Check if task was stopped
                global_task_info = global_task_manager.get_task(task_id)
                if global_task_info and global_task_info.status == 'stopped':
                    raise Exception("Task stopped by user")

                # Verify task_id consistency
                step_task_id = step_data.get('task_id')
                web_task_id = task_id
                if step_task_id and step_task_id != web_task_id:
                    logger.warning(f"⚠️ Task ID mismatch: Web={web_task_id}, Step={step_task_id}")
                else:
                    logger.info(f"✅ Task ID consistent: {web_task_id}")

                # Save step to database if Supabase is available
                logger.info(f"Step callback triggered - SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}, has_save_step: {hasattr(global_task_manager, 'save_step')}")

                if SUPABASE_AVAILABLE and hasattr(global_task_manager, 'save_step'):
                    try:
                        logger.info(f"💾 Attempting to save step {step_data.get('step_number')} to database")

                        # Prepare step record for database
                        step_record = {
                            # 'id' will be auto-generated by database
                            'task_id': step_data.get('task_id'),
                            'step_number': step_data.get('step_number'),
                            'step_type': 'completion' if step_data.get('finished') else 'action',
                            'step_data': {
                                'action': step_data.get('action'),
                                'result': self._serialize_result(step_data.get('result'))
                            },
                            'thinking': step_data.get('thinking'),
                            'action_result': self._serialize_result(step_data.get('result')),
                            'screenshot_path': step_data.get('screenshot_path'),
                            'success': step_data.get('success'),
                            'created_at': datetime.now().isoformat()
                        }

                        # Save step to task_steps table
                        saved_step_id = global_task_manager.save_step(step_record)

                        if saved_step_id:
                            logger.info(f"✅ Step {step_data.get('step_number')} saved successfully with ID: {saved_step_id}")
                        else:
                            logger.error(f"❌ Failed to save step {step_data.get('step_number')} - no ID returned")

                        # Save screenshot information to step_screenshots table
                        screenshot_path = step_data.get('screenshot_path')
                        if screenshot_path and os.path.exists(screenshot_path) and saved_step_id:
                            logger.info(f"📸 Saving screenshot: {screenshot_path}")

                            screenshot_record = {
                                'id': str(uuid.uuid4()),
                                'task_id': step_data.get('task_id'),
                                'step_id': saved_step_id,  # Use the returned step ID
                                'screenshot_path': screenshot_path,
                                'file_size': get_file_size(screenshot_path),
                                'file_hash': calculate_file_hash(screenshot_path),
                                'compressed': False,
                                'created_at': datetime.now().isoformat()
                            }

                            saved_screenshot_id = global_task_manager.save_step_screenshot(screenshot_record)

                            if saved_screenshot_id:
                                logger.info(f"✅ Screenshot saved successfully with ID: {saved_screenshot_id}")
                            else:
                                logger.error(f"❌ Failed to save screenshot")

                            if agent_config.get('verbose', False):
                                print(f"💾 Saved step {step_data.get('step_number')} to database")
                        elif screenshot_path:
                            if not os.path.exists(screenshot_path):
                                logger.warning(f"⚠️ Screenshot file not found: {screenshot_path}")
                            else:
                                logger.warning(f"⚠️ No step_id returned, skipping screenshot save")

                    except Exception as db_error:
                        # Log error but don't interrupt task execution
                        error_msg = f"⚠️ Failed to save step to database: {db_error}"
                        print(error_msg)
                        logger.error(f"Step database save error: {db_error}")
                        logger.exception("Full traceback:")
                else:
                    logger.warning(f"⚠️ Step saving not available. SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}, has_save_step: {hasattr(global_task_manager, 'save_step') if hasattr(global_task_manager, 'save_step') else 'global_task_manager missing save_step'}")
                    if not SUPABASE_AVAILABLE:
                        logger.warning("Supabase is not available - check environment variables and connection")
                    if not hasattr(global_task_manager, 'save_step'):
                        logger.warning("global_task_manager does not have save_step method")

                # Convert non-serializable objects to serializable format
                serializable_step = {
                    'step_number': step_data.get('step_number'),
                    'thinking': step_data.get('thinking'),
                    'action': self._serialize_action(step_data.get('action')),
                    'result': self._serialize_result(step_data.get('result')),
                    'screenshot': step_data.get('screenshot'),
                    'success': step_data.get('success'),
                    'finished': step_data.get('finished')
                }

                self.socketio.emit('step_update', {
                    'session_id': session_id,
                    'step': serializable_step,
                    'task_id': task_id,
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)

            # Execute task
            result = agent.run(task_description, step_callback=step_callback)

            # Save script to database if recording was enabled
            script_id = None
            if agent_config.get('record_script', False) and hasattr(agent, 'recorder') and agent.recorder:
                try:
                    # Finish recording and save to database
                    agent.recorder.finish_recording(success=True)
                    script_id = agent.recorder.save_to_database_and_file()

                    # Update global task with script_id
                    if script_id:
                        global_task_manager.update_task(task_id, script_id=script_id)
                        print(f"Task {task_id} script saved with ID: {script_id}")
                except Exception as script_error:
                    print(f"Failed to save script to database: {script_error}")

            # Update session and global task
            session_data.task_status = 'completed'
            session_data.last_activity = datetime.now()
            global_task_manager.update_task_status(task_id, 'completed', result=str(result))

            # Add result to conversation
            session_data.conversation_history.append({
                'role': 'assistant',
                'content': str(result),
                'timestamp': datetime.now().isoformat()
            })

            # Notify completion
            self.socketio.emit('task_completed', {
                'session_id': session_id,
                'result': str(result),
                'task_id': task_id,
                'script_id': script_id,  # Include script_id in response
                'timestamp': datetime.now().isoformat()
            }, room=session_id)

        except StopException as e:
            # Task was stopped by user
            logger.info(f"🛑 Task {task_id} stopped: {e}")

            # Save script to database if recording was enabled
            script_id = None
            if agent_config.get('record_script', False) and hasattr(agent, 'recorder') and agent.recorder:
                try:
                    # Finish recording and save to database
                    agent.recorder.stop()  # Stop recording
                    script_id = agent.recorder.save_to_database_and_file()

                    # Update global task with script_id
                    if script_id:
                        global_task_manager.update_task(task_id, script_id=script_id)
                        print(f"Task {task_id} script saved with ID: {script_id}")
                except Exception as script_error:
                    print(f"Failed to save script to database: {script_error}")

            # Update session and global task status
            session_data.task_status = 'stopped'
            session_data.last_activity = datetime.now()
            global_task_manager.update_task_status(task_id, 'stopped', result=str(e))

            # Add result to conversation
            session_data.conversation_history.append({
                'role': 'assistant',
                'content': str(e),
                'timestamp': datetime.now().isoformat()
            })

            # Notify stop completion
            self.socketio.emit('task_stopped', {
                'session_id': session_id,
                'result': str(e),
                'task_id': task_id,
                'script_id': script_id,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)

        except Exception as e:
            # Save script to database even if task failed (if recording was enabled)
            script_id = None
            try:
                if 'agent_config' in locals() and agent_config.get('record_script', False) and 'agent' in locals() and hasattr(agent, 'recorder') and agent.recorder:
                    # Finish recording with failure status
                    agent.recorder.finish_recording(success=False)
                    script_id = agent.recorder.save_to_database_and_file()

                    # Update global task with script_id even for failed tasks
                    if script_id:
                        global_task_manager.update_task(task_id, script_id=script_id)
                        print(f"Failed task {task_id} script saved with ID: {script_id}")
            except Exception as script_error:
                print(f"Failed to save script to database during error handling: {script_error}")

            # Handle error
            session_data.task_status = 'error'
            session_data.last_activity = datetime.now()
            global_task_manager.update_task_status(task_id, 'error', str(e))

            error_message = str(e)
            session_data.conversation_history.append({
                'role': 'assistant',
                'content': f'Error: {error_message}',
                'timestamp': datetime.now().isoformat()
            })

            self.socketio.emit('task_error', {
                'session_id': session_id,
                'error': error_message,
                'task_id': task_id,
                'script_id': script_id,  # Include script_id even for errors
                'timestamp': datetime.now().isoformat()
            }, room=session_id)

    def _create_agent_config(self, config: Dict) -> Dict:
        """Create agent configuration from request"""
        # Start with default config
        agent_config = self.agent_configs.get('default', {}).copy()

        # Update with provided config
        agent_config.update(config)

        return agent_config

    def _serialize_action(self, action):
        """Serialize action object to JSON-compatible format"""
        if action is None:
            return None
        if isinstance(action, dict):
            return action
        # Try to convert object to dict
        try:
            if hasattr(action, '__dict__'):
                return action.__dict__
            else:
                return str(action)
        except Exception:
            return str(action)

    def _serialize_result(self, result):
        """Serialize result object to JSON-compatible format"""
        if result is None:
            return None
        # Try to convert object to dict
        try:
            if hasattr(result, '__dict__'):
                # Extract key attributes
                result_dict = {}
                if hasattr(result, 'success'):
                    result_dict['success'] = result.success
                if hasattr(result, 'message'):
                    result_dict['message'] = result.message
                if hasattr(result, 'error'):
                    result_dict['error'] = result.error
                return result_dict
            else:
                return str(result)
        except Exception:
            return str(result)

    def run(self):
        """Run the web application"""
        print(f"Starting Phone Agent Web Interface...")
        print(f"Server: http://{self.host}:{self.port}")
        print(f"Debug mode: {self.debug}")

        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            allow_unsafe_werkzeug=True
        )


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Phone Agent Web Interface")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Create and run web app
    web_app = PhoneAgentWeb(host=args.host, port=args.port, debug=args.debug)
    web_app.run()


if __name__ == '__main__':
    main()