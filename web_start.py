#!/usr/bin/env python3
"""
Phone Agent Web Interface Launcher
Quick start script for the Phone Agent web interface
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['flask', 'flask-socketio']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies are installed")
    return True


def check_adb_connection():
    """Check if ADB devices are connected"""
    try:
        # Add parent directory to path for imports
        parent_dir = Path(__file__).parent
        sys.path.insert(0, str(parent_dir))

        from phone_agent.adb import list_devices
        devices = list_devices()

        if not devices:
            print("⚠️  No ADB devices found")
            print("Please ensure:")
            print("1. Device is connected via USB")
            print("2. USB debugging is enabled")
            print("3. Device is authorized")
            return False
        else:
            print(f"✅ Found {len(devices)} device(s):")
            for device in devices:
                print(f"   - {device.device_id} ({device.connection_type.value})")
            return True

    except Exception as e:
        print(f"⚠️  Could not check ADB devices: {e}")
        return True  # Don't block startup for ADB issues


def check_model_service(base_url=None):
    """Check if model service is available"""
    try:
        import os
        import requests

        # Load .env file
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

        # Use environment variable if no base_url provided
        if base_url is None:
            base_url = os.getenv('PHONE_AGENT_BASE_URL', 'http://localhost:8000/v1')

        print(f"🧠 Checking model service at: {base_url}")

        # For BigModel API, check with a different endpoint
        if 'bigmodel.cn' in base_url:
            # Test by sending a simple chat request
            headers = {
                'Authorization': f'Bearer {os.getenv("PHONE_AGENT_API_KEY", "")}',
                'Content-Type': 'application/json'
            }
            data = {
                "model": "glm-4-flash",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }

            response = requests.post(f"{base_url}/chat/completions",
                                   headers=headers,
                                   json=data,
                                   timeout=10)
            if response.status_code == 200:
                print("✅ BigModel API service is available")
                return True
            else:
                print(f"⚠️  BigModel API returned status {response.status_code}")
                return False
        else:
            # For local/other model services, check /models endpoint
            response = requests.get(f"{base_url}/models", timeout=5)
            if response.status_code == 200:
                print("✅ Model service is available")
                return True
            else:
                print(f"⚠️  Model service returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"⚠️  Could not connect to model service: {e}")
        print("The web interface will still start, but tasks may fail until the model service is available")
        return False


def start_web_server(host='0.0.0.0', port=5000, debug=False):
    """Start the web server"""
    print(f"\n🚀 Starting Phone Agent Web Interface...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   URL: http://{host}:{port}")
    print()

    # Add parent directory to path for imports
    parent_dir = Path(__file__).parent
    sys.path.insert(0, str(parent_dir))

    # Change to web directory
    web_dir = Path(__file__).parent / 'web'
    if web_dir.exists():
        os.chdir(web_dir)

    try:
        # Import and run the web app
        # Make sure the web directory is in the Python path
        if str(Path.cwd()) not in sys.path:
            sys.path.insert(0, str(Path.cwd()))

        # Also add parent directory to path for importing phone_agent modules
        if str(Path.cwd().parent) not in sys.path:
            sys.path.insert(0, str(Path.cwd().parent))

        print(f"Python path: {sys.path[:3]}")

        from app import PhoneAgentWeb

        web_app = PhoneAgentWeb(host=host, port=port, debug=debug)
        web_app.run()

    except KeyboardInterrupt:
        print("\n👋 Shutting down web server...")
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Phone Agent Web Interface Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python web_start.py                    # Start with default settings
  python web_start.py --port 8080        # Start on port 8080
  python web_start.py --debug            # Start with debug mode
  python web_start.py --skip-checks      # Skip dependency checks
        """
    )

    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency and device checks')
    parser.add_argument('--model-url', default='http://localhost:8000/v1', help='Model service URL to check')

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 Phone Agent Web Interface Launcher")
    print("=" * 60)

    # Run checks unless skipped
    if not args.skip_checks:
        print("\n📋 Checking dependencies...")
        if not check_dependencies():
            sys.exit(1)

        print("\n📱 Checking ADB devices...")
        check_adb_connection()

        print("\n🧠 Checking model service...")
        check_model_service()
    else:
        print("\n⏭️  Skipping checks as requested")

    # Start the web server
    start_web_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()