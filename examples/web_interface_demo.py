#!/usr/bin/env python3
"""
Phone Agent Web Interface Demo
Demonstrates how to use the web interface programmatically
"""

import sys
import time
import requests
import socketio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_web_interface():
    """Test the web interface programmatically"""

    print("🌐 Phone Agent Web Interface Demo")
    print("=" * 50)

    # Check if web interface is running
    base_url = "http://localhost:5000"

    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Web interface is running at:", base_url)
        else:
            print(f"⚠️  Web interface returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to web interface: {e}")
        print("Please start the web interface first:")
        print("  python web_start.py")
        return False

    # Test API endpoints
    print("\n📋 Testing API endpoints...")

    # Test session creation
    try:
        response = requests.post(
            f"{base_url}/api/sessions",
            json={"user_id": "demo_user"},
            timeout=5
        )
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Session created: {session_id[:8]}...")
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False

    # Test device listing
    try:
        response = requests.get(f"{base_url}/api/devices", timeout=5)
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Found {len(devices)} devices:")
            for device in devices:
                print(f"   - {device['device_id']} ({device['connection_type']})")
        else:
            print(f"⚠️  Device listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Device listing error: {e}")

    # Test app listing
    try:
        response = requests.get(f"{base_url}/api/apps", timeout=5)
        if response.status_code == 200:
            apps = response.json()
            print(f"✅ Found {len(apps)} supported apps")
            if apps:
                print(f"   Sample apps: {', '.join(apps[:5])}...")
        else:
            print(f"⚠️  App listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ App listing error: {e}")

    # Test WebSocket connection
    print("\n🔌 Testing WebSocket connection...")
    try:
        sio = socketio.Client()

        connected = False

        @sio.event
        def connect():
            nonlocal connected
            connected = True
            print("✅ WebSocket connected successfully")

        @sio.event
        def disconnect():
            print("🔌 WebSocket disconnected")

        sio.connect(base_url)

        if connected:
            # Test joining session
            sio.emit('join_session', {'session_id': session_id})
            print("✅ Joined session room")

            # Wait a bit
            time.sleep(1)

            # Disconnect
            sio.disconnect()
        else:
            print("❌ WebSocket connection failed")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")

    print("\n🎉 Web interface demo completed!")
    print("\n📖 Usage instructions:")
    print("1. Start web interface: python web_start.py")
    print("2. Open browser: http://localhost:5000")
    print("3. Configure model settings in the config page")
    print("4. Start chatting with the Phone Agent!")

    return True


def demonstrate_features():
    """Demonstrate key features"""

    print("\n🚀 Key Features Demo")
    print("=" * 50)

    features = [
        {
            'name': '多轮对话',
            'description': '支持连续的对话交互，记忆上下文',
            'example': '用户: 打开微信 -> 助手: 已打开微信 -> 用户: 查看未读消息'
        },
        {
            'name': '实时状态',
            'description': '实时显示任务执行状态和进度',
            'example': '执行中... 步骤 3/10: 点击搜索框'
        },
        {
            'name': '截图显示',
            'description': '实时显示操作过程中的手机截图',
            'example': '📱 显示当前手机界面截图'
        },
        {
            'name': '配置管理',
            'description': '可视化配置模型和设备参数',
            'example': '模型: autoglm-phone, 设备: USB连接'
        },
        {
            'name': '脚本记录',
            'description': '自动记录操作并生成可重放脚本',
            'example': '生成 JSON 和 Python 重放脚本'
        }
    ]

    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['name']}")
        print(f"   {feature['description']}")
        print(f"   示例: {feature['example']}")


def show_quick_start():
    """Show quick start guide"""

    print("\n⚡ Quick Start Guide")
    print("=" * 50)

    steps = [
        "安装依赖: pip install -r requirements-web.txt",
        "启动服务: python web_start.py",
        "打开浏览器: http://localhost:5000",
        "配置模型: 访问配置页面设置模型参数",
        "开始使用: 在聊天界面输入任务描述"
    ]

    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")

    print("\n📱 Example tasks you can try:")
    print("- 打开微信查看未读消息")
    print("- 打开淘宝搜索无线耳机")
    print("- 打开美团搜索附近的火锅店")
    print("- 打开设置调整音量到最大")


if __name__ == '__main__':
    print("🤖 Phone Agent Web Interface Demo")
    print("🎯 Demonstrating the modern web interface for phone automation")
    print()

    # Run main demo
    success = test_web_interface()

    if success:
        demonstrate_features()
        show_quick_start()
    else:
        print("\n❌ Demo failed. Please ensure the web interface is running:")
        print("   python web_start.py")
        sys.exit(1)