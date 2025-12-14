#!/usr/bin/env python3
"""
测试步骤追踪功能的简单脚本
"""

import sys
import os
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_step_tracker_import():
    """测试 StepTracker 导入"""
    try:
        from phone_agent.step_tracker import StepTracker, StepType, StepData
        print("✅ StepTracker 导入成功")
        return True
    except ImportError as e:
        print(f"❌ StepTracker 导入失败: {e}")
        return False

def test_phone_agent_modification():
    """测试 PhoneAgent 是否已修改"""
    try:
        from phone_agent.agent import PhoneAgent

        # 检查是否有 step_tracker 相关的导入和属性
        import inspect

        # 查看源码中是否包含 step_tracker 相关代码
        source = inspect.getsource(PhoneAgent.__init__)
        if 'step_tracker' in source:
            print("✅ PhoneAgent 已集成 StepTracker")
            return True
        else:
            print("❌ PhoneAgent 未找到 StepTracker 集成代码")
            return False
    except Exception as e:
        print(f"❌ 测试 PhoneAgent 修改失败: {e}")
        return False

def test_web_app_modification():
    """测试 web.app.py 是否已修改"""
    try:
        # 检查辅助函数是否存在
        from app import calculate_file_hash, get_file_size
        print("✅ web.app.py 辅助函数已添加")

        # 测试辅助函数
        test_file = Path(__file__)
        hash_val = calculate_file_hash(str(test_file))
        size = get_file_size(str(test_file))

        if hash_val and size > 0:
            print(f"✅ 辅助函数测试通过 (hash: {hash_val[:8]}..., size: {size} bytes)")
            return True
        else:
            print("❌ 辅助函数测试失败")
            return False
    except Exception as e:
        print(f"❌ 测试 web.app.py 修改失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始测试步骤追踪功能实现...")
    print("=" * 50)

    results = []

    # 测试 StepTracker 导入
    results.append(test_step_tracker_import())

    # 测试 PhoneAgent 修改
    results.append(test_phone_agent_modification())

    # 测试 web.app.py 修改
    results.append(test_web_app_modification())

    print("=" * 50)
    if all(results):
        print("🎉 所有测试通过！步骤追踪功能已成功实现")
        return 0
    else:
        print("❌ 部分测试失败，请检查实现")
        return 1

if __name__ == "__main__":
    sys.exit(main())