#!/usr/bin/env python3
"""
启用脚本记录功能 - 修改Web应用默认配置
"""
import re

def enable_script_recording():
    """修改Web应用配置以默认启用脚本记录"""

    app_py_path = "web/app.py"

    try:
        # 读取app.py文件
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找record_script配置
        old_config = "                'record_script': False,"
        new_config = "                'record_script': True,"  # 默认启用脚本记录

        if old_config in content:
            # 替换配置
            updated_content = content.replace(old_config, new_config)

            # 写回文件
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print("✅ 已将脚本记录功能设为默认启用")
            print("✅ 配置修改位置: web/app.py")
            print("\n现在重新运行任务时将自动记录脚本到数据库")
            return True
        else:
            print("❌ 未找到record_script配置，可能已被修改")
            print(f"查找的配置: {old_config}")
            return False

    except Exception as e:
        print(f"❌ 修改配置失败: {e}")
        return False

def update_task_config_endpoint():
    """修改任务配置API以支持脚本记录"""

    app_py_path = "web/app.py"

    try:
        # 读取app.py文件
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找配置API端点
        old_endpoint = """        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            \"\"\"Get current configuration\"\"\"
            return jsonify({
                'data': {
                    'api_key': os.getenv('PHONE_AGENT_API_KEY', 'EMPTY'),
                    'max_steps': 100,
                    'device_id': None,
                    'lang': 'cn',
                    'verbose': True,
                    'record_script': False,
                    'script_output_dir': 'web_scripts'
                }
            })"""

        new_endpoint = """        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            \"\"\"Get current configuration\"\"\"
            return jsonify({
                'data': {
                    'api_key': os.getenv('PHONE_AGENT_API_KEY', 'EMPTY'),
                    'max_steps': 100,
                    'device_id': None,
                    'lang': 'cn',
                    'verbose': True,
                    'record_script': True,  # 默认启用脚本记录
                    'script_output_dir': 'web_scripts'
                }
            })"""

        if old_endpoint in content:
            # 替换端点
            updated_content = content.replace(old_endpoint, new_endpoint)

            # 写回文件
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print("✅ 已更新配置API端点")
            return True
        else:
            print("⚠️ 配置API端点可能已被修改或不存在")
            return False

    except Exception as e:
        print(f"❌ 更新API端点失败: {e}")
        return False

if __name__ == "__main__":
    print("=== Open-AutoGLM 脚本记录启用工具 ===")

    print("\n步骤1: 修改默认配置...")
    config_success = enable_script_recording()

    print("\n步骤2: 更新配置API...")
    api_success = update_task_config_endpoint()

    if config_success and api_success:
        print("\n🎉 脚本记录功能启用成功！")
        print("\n接下来请:")
        print("1. 重启Web服务: python3 web/app.py --port 8080")
        print("2. 在Web界面执行任务")
        print("3. 任务完成后查看: http://localhost:8080/api/scripts")
    else:
        print("\n⚠️ 部分修改可能失败，请检查上述输出")
        print("\n您可以手动:")
        print("1. 在Web界面配置中启用'记录脚本'选项")
        print("2. 或者直接修改web/app.py中的record_script配置")