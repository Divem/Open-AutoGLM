#!/usr/bin/env python3
"""
测试 StepTracker.record_step 修复
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_record_step_parameters():
    """测试 record_step 方法调用参数是否正确"""
    try:
        from phone_agent.step_tracker import StepTracker, StepType
        import uuid

        # 创建一个测试用的 StepTracker
        task_id = str(uuid.uuid4())
        tracker = StepTracker(task_id)

        # 测试正确的 record_step 调用
        tracker.record_step(
            step_type=StepType.ACTION,
            step_data={
                'action': {'type': 'click', 'element': 'button'},
                'result': {'success': True, 'message': 'Clicked button'}
            },
            thinking="Click the button to proceed",
            action_result={'success': True, 'message': 'Action completed'},
            screenshot_path="/path/to/screenshot.png",
            success=True
        )

        print("✅ record_step 方法调用成功")
        return True

    except Exception as e:
        print(f"❌ record_step 调用失败: {e}")
        return False

def test_wrong_call():
    """测试错误的调用方式（应该失败）"""
    try:
        from phone_agent.step_tracker import StepTracker, StepType, StepData
        import uuid

        task_id = str(uuid.uuid4())
        tracker = StepTracker(task_id)

        # 创建 StepData 对象
        step_data = StepData(
            step_id=str(uuid.uuid4()),
            task_id=task_id,
            step_number=1,
            step_type=StepType.ACTION,
            step_data={'action': 'test'},
            thinking='test thinking'
        )

        # 尝试传递 StepData 对象（这应该失败）
        try:
            tracker.record_step(step_data)
            print("❌ 预期应该失败，但却成功了")
            return False
        except TypeError as e:
            print(f"✅ 正确拒绝了 StepData 对象: {str(e)[:100]}...")
            return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试 StepTracker.record_step 修复...")
    print("=" * 50)

    results = []

    # 测试 1: 正确的参数调用
    results.append(test_record_step_parameters())

    # 测试 2: 错误的调用方式
    results.append(test_wrong_call())

    print("=" * 50)
    if all(results):
        print("🎉 所有测试通过！record_step 参数问题已修复")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())