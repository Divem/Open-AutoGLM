#!/usr/bin/env python3
"""
测试停止机制的简单脚本
"""

import sys
import time
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phone_agent.stop_handler import StopSignalHandler, StopException, StopReason


def test_stop_signal_handler():
    """测试停止信号处理器"""
    print("🧪 测试停止信号处理器...")

    handler = StopSignalHandler()

    # 初始状态应该是未停止
    assert not handler.should_stop(), "初始状态应该是未停止"
    print("✅ 初始状态检查通过")

    # 测试停止
    handler.stop(StopReason.USER_REQUEST, "测试停止")
    assert handler.should_stop(), "停止后应该是已停止状态"
    print("✅ 停止功能检查通过")

    # 测试停止信息
    stop_info = handler.get_stop_info()
    assert stop_info is not None, "停止信息不应该为None"
    assert stop_info.reason == StopReason.USER_REQUEST, "停止原因应该匹配"
    print("✅ 停止信息检查通过")

    # 测试重置
    handler.reset()
    assert not handler.should_stop(), "重置后应该是未停止状态"
    print("✅ 重置功能检查通过")

    print("🎉 停止信号处理器测试通过！")


def test_stop_exception():
    """测试停止异常"""
    print("\n🧪 测试停止异常...")

    handler = StopSignalHandler()

    try:
        handler.check_stop()
        print("✅ 未停止状态下check_stop应该正常")
    except StopException:
        assert False, "未停止状态下不应该抛出异常"

    handler.stop(StopReason.TIMEOUT, "超时测试")

    try:
        handler.check_stop()
        assert False, "已停止状态下应该抛出异常"
    except StopException as e:
        assert "超时测试" in str(e), "异常消息应该包含停止消息"
        print("✅ 停止异常检查通过")

    print("🎉 停止异常测试通过！")


def test_concurrent_stop():
    """测试并发停止"""
    print("\n🧪 测试并发停止...")

    handler = StopSignalHandler()
    results = []

    def worker():
        try:
            for i in range(10):
                if handler.should_stop():
                    results.append(f"Worker stopped at iteration {i}")
                    return
                time.sleep(0.1)
            results.append("Worker completed normally")
        except Exception as e:
            results.append(f"Worker error: {e}")

    # 启动工作线程
    thread = threading.Thread(target=worker)
    thread.start()

    # 0.3秒后发送停止信号
    time.sleep(0.3)
    handler.stop(StopReason.USER_REQUEST, "并发测试停止")

    # 等待线程完成
    thread.join(timeout=1.0)

    assert thread.is_alive() == False, "线程应该已经停止"
    assert len(results) > 0, "应该有结果"
    assert "stopped at iteration" in results[0], "应该记录停止时的迭代"
    print(f"✅ 并发停止测试通过: {results[0]}")

    print("🎉 并发停止测试通过！")


def test_phone_agent_integration():
    """测试PhoneAgent集成"""
    print("\n🧪 测试PhoneAgent集成...")

    try:
        from phone_agent.agent import PhoneAgent
        from phone_agent.model import ModelConfig
        from phone_agent.stop_handler import StopReason

        # 创建PhoneAgent实例
        model_config = ModelConfig()
        agent = PhoneAgent(model_config=model_config)

        # 检查是否有停止处理器
        assert hasattr(agent, 'stop_handler'), "PhoneAgent应该有stop_handler属性"
        assert hasattr(agent, 'stop'), "PhoneAgent应该有stop方法"
        assert hasattr(agent, 'should_stop'), "PhoneAgent应该有should_stop方法"
        print("✅ PhoneAgent停止方法检查通过")

        # 测试停止功能
        assert not agent.should_stop(), "初始状态应该是未停止"
        agent.stop(StopReason.USER_REQUEST, "集成测试停止")
        assert agent.should_stop(), "停止后应该是已停止状态"
        print("✅ PhoneAgent停止功能检查通过")

        print("🎉 PhoneAgent集成测试通过！")

    except ImportError as e:
        print(f"⚠️ 跳过PhoneAgent集成测试，导入失败: {e}")


def test_model_client_integration():
    """测试ModelClient集成"""
    print("\n🧪 测试ModelClient集成...")

    try:
        from phone_agent.model.client import ModelClient, ModelConfig
        from phone_agent.stop_handler import StopSignalHandler

        # 创建带停止处理器的ModelClient
        config = ModelConfig()
        stop_handler = StopSignalHandler()
        client = ModelClient(config=config, stop_handler=stop_handler)

        # 检查是否有停止处理器
        assert hasattr(client, 'stop_handler'), "ModelClient应该有stop_handler属性"
        assert client.stop_handler is stop_handler, "停止处理器应该正确设置"
        print("✅ ModelClient停止处理器检查通过")

        print("🎉 ModelClient集成测试通过！")

    except ImportError as e:
        print(f"⚠️ 跳过ModelClient集成测试，导入失败: {e}")


def main():
    """运行所有测试"""
    print("🚀 开始停止机制测试...\n")

    try:
        test_stop_signal_handler()
        test_stop_exception()
        test_concurrent_stop()
        test_phone_agent_integration()
        test_model_client_integration()

        print("\n🎊 所有测试通过！停止机制工作正常。")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())