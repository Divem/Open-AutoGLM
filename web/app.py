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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig
from phone_agent.recorder import ScriptRecorder


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


class GlobalTaskManager:
    """Global task manager that persists across page refreshes"""

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
try:
    from supabase_manager import SupabaseTaskManager
    global_task_manager = SupabaseTaskManager()
    print("✅ Supabase任务管理器初始化成功")
except Exception as e:
    print(f"❌ Supabase任务管理器初始化失败: {e}")
    print("回退到本地存储...")

    # 如果Supabase失败，使用本地存储
    global_task_manager = GlobalTaskManager()
    print("✅ 本地任务管理器初始化成功")


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

        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

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
                'record_script': False,
                'script_output_dir': 'web_scripts'
            }
        }

        # Setup routes
        self.setup_routes()
        self.setup_socketio()

    def setup_routes(self):
        """Setup Flask routes"""

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
            """Serve screenshot files"""
            return send_from_directory(self.app.config['SCREENSHOTS_FOLDER'], filename)

        @self.app.route('/uploads/<path:filename>')
        def serve_upload(filename):
            """Serve uploaded files"""
            return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename)

        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get all tasks"""
            session_id = request.args.get('session_id')
            if session_id:
                tasks = global_task_manager.get_tasks_by_session(session_id)
            else:
                tasks = global_task_manager.get_all_tasks()

            return jsonify([{
                'task_id': task.task_id,
                'session_id': task.session_id,
                'user_id': task.user_id,
                'task_description': task.task_description,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'last_activity': task.last_activity.isoformat(),
                'error_message': task.error_message
            } for task in tasks])

        @self.app.route('/api/tasks/<task_id>/stop', methods=['POST'])
        def stop_task(task_id):
            """Stop a running task"""
            success = global_task_manager.stop_task(task_id)
            if success:
                return jsonify({'message': 'Task stopped successfully'})
            else:
                return jsonify({'error': 'Task not found or cannot be stopped'}), 404

        @self.app.route('/api/tasks/<task_id>', methods=['GET'])
        def get_task(task_id):
            """Get task by ID"""
            task = global_task_manager.get_task(task_id)
            if task:
                return jsonify({
                    'task_id': task.task_id,
                    'session_id': task.session_id,
                    'user_id': task.user_id,
                    'task_description': task.task_description,
                    'status': task.status,
                    'created_at': task.created_at.isoformat(),
                    'last_activity': task.last_activity.isoformat(),
                    'error_message': task.error_message,
                    'config': task.config
                })
            else:
                return jsonify({'error': 'Task not found'}), 404

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
                session_data.task_status = 'stopped'

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
                agent_config=agent_config_obj
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

            # Update session and global task
            session_data.task_status = 'completed'
            session_data.last_activity = datetime.now()
            global_task_manager.update_task_status(task_id, 'completed')

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
                'timestamp': datetime.now().isoformat()
            }, room=session_id)

        except Exception as e:
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