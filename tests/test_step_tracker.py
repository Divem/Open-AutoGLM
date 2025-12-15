#!/usr/bin/env python3
"""
测试 StepTracker 功能
"""

import unittest
import tempfile
import os
from datetime import datetime
from phone_agent.step_tracker import StepTracker, StepData, StepType

class TestStepTracker(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.task_id = "test_task_123"
        self.tracker = StepTracker(self.task_id, buffer_size=5, flush_interval=0.1)

    def tearDown(self):
        """清理测试环境"""
        self.tracker.cleanup()

    def test_step_data_creation(self):
        """测试步骤数据创建"""
        step = StepData(
            step_id="step_1",
            task_id=self.task_id,
            step_number=1,
            step_type=StepType.ACTION,
            step_data={"action": "click"},
            success=True
        )

        self.assertEqual(step.step_type, StepType.ACTION)
        self.assertEqual(step.step_number, 1)
        self.assertTrue(step.success)

    def test_step_data_serialization(self):
        """测试步骤数据序列化"""
        step = StepData(
            step_id="step_1",
            task_id=self.task_id,
            step_number=1,
            step_type=StepType.ACTION,
            step_data={"action": "click"},
            thinking="Test thinking",
            success=True
        )

        # 转换为字典
        step_dict = step.to_dict()
        self.assertIsInstance(step_dict, dict)
        self.assertEqual(step_dict['step_type'], 'action')
        self.assertIsInstance(step_dict['timestamp'], str)

        # 从字典恢复
        restored_step = StepData.from_dict(step_dict)
        self.assertEqual(restored_step.step_type, StepType.ACTION)
        self.assertEqual(restored_step.thinking, "Test thinking")

    def test_record_step(self):
        """测试记录步骤"""
        self.tracker.record_step(
            step_type=StepType.ACTION,
            step_data={"action": "click_button"},
            thinking="Clicking the button",
            success=True
        )

        steps = self.tracker.get_steps()
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].step_type, StepType.ACTION)
        self.assertEqual(steps[0].thinking, "Clicking the button")
        self.assertTrue(steps[0].success)

    def test_multiple_steps(self):
        """测试记录多个步骤"""
        # 记录多个步骤
        for i in range(3):
            self.tracker.record_step(
                step_type=StepType.ACTION,
                step_data={"step": i + 1},
                success=i != 1  # 第二个步骤失败
            )

        steps = self.tracker.get_steps()
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].step_number, 1)
        self.assertEqual(steps[1].step_number, 2)
        self.assertEqual(steps[2].step_number, 3)

        # 检查成功/失败统计
        self.assertTrue(steps[0].success)
        self.assertFalse(steps[1].success)
        self.assertTrue(steps[2].success)

    def test_screenshot_recording(self):
        """测试截图记录"""
        # 创建临时截图文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake screenshot data')
            screenshot_path = f.name

        try:
            self.tracker.record_step(
                step_type=StepType.SCREENSHOT,
                step_data={"action": "take_screenshot"},
                screenshot_path=screenshot_path
            )

            steps = self.tracker.get_steps()
            self.assertEqual(len(steps), 1)
            self.assertEqual(steps[0].screenshot_path, screenshot_path)

            # 检查截图信息
            screenshots = self.tracker.screenshots
            self.assertEqual(len(screenshots), 1)
            self.assertTrue(screenshot_path in screenshots)
            self.assertGreater(screenshots[screenshot_path].file_size, 0)
            self.assertIsNot(screenshots[screenshot_path].file_hash, "")

        finally:
            # 清理临时文件
            if os.path.exists(screenshot_path):
                os.unlink(screenshot_path)

    def test_statistics(self):
        """测试统计信息"""
        # 记录一些步骤
        self.tracker.record_step(StepType.ACTION, {"a": 1}, success=True)
        self.tracker.record_step(StepType.THINKING, {"t": 1}, success=True)
        self.tracker.record_step(StepType.ERROR, {"e": 1}, success=False, error_message="Test error")

        stats = self.tracker.get_statistics()
        self.assertEqual(stats['total_steps'], 3)
        self.assertEqual(stats['successful_steps'], 2)
        self.assertEqual(stats['failed_steps'], 1)
        self.assertAlmostEqual(stats['success_rate'], 2/3, places=2)

    def test_enable_disable(self):
        """测试启用/禁用功能"""
        # 禁用跟踪
        self.tracker.disable()
        self.tracker.record_step(StepType.ACTION, {"a": 1}, success=True)
        self.assertEqual(len(self.tracker.get_steps()), 0)

        # 重新启用
        self.tracker.enable()
        self.tracker.record_step(StepType.ACTION, {"a": 2}, success=True)
        self.assertEqual(len(self.tracker.get_steps()), 1)

    def test_step_callback(self):
        """测试步骤回调"""
        callback_steps = []

        def test_callback(step):
            callback_steps.append(step)

        self.tracker.add_step_callback(test_callback)
        self.tracker.record_step(StepType.ACTION, {"a": 1}, success=True)

        self.assertEqual(len(callback_steps), 1)
        self.assertEqual(callback_steps[0].step_type, StepType.ACTION)

    def test_buffer_flush(self):
        """测试缓冲区刷新"""
        # 记录多个步骤，触发缓冲区刷新
        for i in range(6):  # 超过缓冲区大小(5)
            self.tracker.record_step(
                StepType.ACTION,
                {"step": i},
                success=True
            )

        # 等待异步刷新完成
        import time
        time.sleep(0.2)

        # 检查所有步骤都被记录
        steps = self.tracker.get_steps()
        self.assertEqual(len(steps), 6)


if __name__ == '__main__':
    unittest.main()