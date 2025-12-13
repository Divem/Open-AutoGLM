#!/usr/bin/env python3
"""
测试 Web 环境下的任务执行
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
os.environ['PHONE_AGENT_BASE_URL'] = 'https://open.bigmodel.cn/api/paas/v4'
os.environ['PHONE_AGENT_MODEL'] = 'autoglm-phone'
os.environ['PHONE_AGENT_API_KEY'] = '272d17c651ad436e93773578a2b6b77f.yiph4Vf2l423BDIA'

def test_web_task_execution():
    """测试 Web 环境下的任务执行"""
    print("🌐 测试 Web 环境任务执行...")

    try:
        from phone_agent import PhoneAgent
        from phone_agent.model import ModelConfig
        from phone_agent.agent import AgentConfig
        print("✅ 成功导入 PhoneAgent 模块")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

    try:
        # 创建配置 (与 Web 应用相同的配置)
        model_config = ModelConfig(
            base_url=os.environ.get('PHONE_AGENT_BASE_URL', 'http://localhost:8000/v1'),
            api_key=os.environ.get('PHONE_AGENT_API_KEY', 'EMPTY'),
            model_name=os.environ.get('PHONE_AGENT_MODEL', 'autoglm-phone-9b')
        )

        agent_config = AgentConfig(
            max_steps=5,  # 限制步数以快速测试
            device_id=None,
            lang='cn',
            verbose=True,
            record_script=False,
            script_output_dir='web_scripts'
        )

        print(f"📋 配置信息:")
        print(f"   - API地址: {model_config.base_url}")
        print(f"   - 模型名称: {model_config.model_name}")
        print(f"   - API密钥: {model_config.api_key[:10]}..." if len(model_config.api_key) > 10 else f"   - API密钥: {model_config.api_key}")

        # 创建代理
        print("\n🤖 创建 PhoneAgent...")
        agent = PhoneAgent(
            model_config=model_config,
            agent_config=agent_config
        )
        print("✅ PhoneAgent 创建成功")

        # 执行一个简单任务
        task = "检查当前设备状态"
        print(f"\n📝 执行任务: {task}")

        result = agent.run(task)
        print(f"🎯 执行结果: {result}")

        return True

    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Web 环境任务执行测试")
    print("=" * 50)

    success = test_web_task_execution()

    if success:
        print("\n🎉 Web 环境任务执行测试成功！")
    else:
        print("\n❌ Web 环境任务执行测试失败！")