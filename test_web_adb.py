#!/usr/bin/env python3
"""
测试 Web 服务是否能正确访问 ADB 设备
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import subprocess
    print("✅ 成功导入模块")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def test_adb_access():
    """测试 ADB 访问"""
    print("\n📱 测试 ADB 访问...")

    try:
        # 测试基本 ADB 命令
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ADB 命令执行成功")
            lines = result.stdout.strip().split('\n')
            devices = [line for line in lines[1:] if line.strip() and '\tdevice' in line]
            print(f"✅ 找到 {len(devices)} 个设备")

            for device_line in devices:
                device_id = device_line.split('\t')[0]
                print(f"   - 设备ID: {device_id}")

                # 测试截图权限
                try:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', 'echo', 'test'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"     ✅ 设备权限正常")
                    else:
                        print(f"     ❌ 设备权限异常: {result.stderr}")
                except subprocess.TimeoutExpired:
                    print(f"     ❌ 设备访问超时")
                except Exception as e:
                    print(f"     ❌ 设备访问失败: {e}")
        else:
            print(f"❌ ADB 命令失败: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ ADB 命令未找到，请安装 Android SDK Platform Tools")
        return False
    except Exception as e:
        print(f"❌ ADB 访问失败: {e}")
        return False

    return True

def test_environment():
    """测试环境变量"""
    print("\n🔧 测试环境变量...")

    base_url = os.getenv('PHONE_AGENT_BASE_URL', 'http://localhost:8000/v1')
    model_name = os.getenv('PHONE_AGENT_MODEL', 'autoglm-phone-9b')
    api_key = os.getenv('PHONE_AGENT_API_KEY', 'EMPTY')

    print(f"   - BASE_URL: {base_url}")
    print(f"   - MODEL: {model_name}")
    print(f"   - API_KEY: {api_key[:10]}..." if len(api_key) > 10 else f"   - API_KEY: {api_key}")

if __name__ == "__main__":
    print("🔍 Web 服务 ADB 权限测试")
    print("=" * 50)

    # 测试环境
    test_environment()

    # 测试 ADB 访问
    success = test_adb_access()

    if success:
        print("\n🎉 所有测试通过！Web 服务应该可以正常工作。")
    else:
        print("\n❌ ADB 访问测试失败，需要检查权限问题。")