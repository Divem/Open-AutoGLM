#!/usr/bin/env python3
"""
测试连续任务模式的脚本
用于验证优化后的 Open-AutoGLM 是否支持连续执行多个任务
"""

import subprocess
import time
import threading

def run_test():
    """测试连续任务模式"""
    print("🧪 开始测试连续任务模式...")
    print("=" * 50)

    # 测试命令：先打开设置，然后应该提示继续
    test_command = [
        "python3", "main.py",
        "打开设置"
    ]

    print(f"📝 执行命令: {' '.join(test_command)}")
    print("⏳ 等待程序启动...")

    try:
        # 启动程序
        process = subprocess.Popen(
            test_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # 模拟连续输入
        def send_inputs():
            time.sleep(15)  # 等待第一个任务完成

            print("🔄 输入第一个后续任务: 打开抖音")
            process.stdin.write("打开抖音\n")
            process.stdin.flush()

            time.sleep(20)  # 等待第二个任务完成

            print("🔄 输入第二个后续任务: 查看设备信息")
            process.stdin.write("查看设备信息\n")
            process.stdin.flush()

            time.sleep(15)  # 等待第三个任务完成

            print("🛑 输入结束命令: 结束任务")
            process.stdin.write("结束任务\n")
            process.stdin.flush()

        # 在后台线程中发送输入
        input_thread = threading.Thread(target=send_inputs)
        input_thread.daemon = True
        input_thread.start()

        # 读取输出
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_lines.append(line.strip())
            print(f"📱 {line.strip()}")

            # 检查是否出现了连续任务模式提示
            if "连续任务模式已启动" in line:
                print("✅ 检测到连续任务模式启动！")
            elif "请输入下一个任务" in line:
                print("✅ 检测到新任务提示！")

        # 等待进程结束
        return_code = process.wait()
        input_thread.join(timeout=1)

        print(f"\n🏁 测试完成，返回码: {return_code}")

        # 分析输出
        continuous_mode_detected = any("连续任务模式" in line for line in output_lines)
        new_task_prompt_detected = any("请输入下一个任务" in line for line in output_lines)
        exit_command_detected = any("再见" in line and "Open-AutoGLM" in line for line in output_lines)

        print("\n📊 测试结果分析:")
        print(f"   ✅ 连续任务模式启动: {'✅' if continuous_mode_detected else '❌'}")
        print(f"   ✅ 新任务提示显示: {'✅' if new_task_prompt_detected else '❌'}")
        print(f"   ✅ 结束命令响应: {'✅' if exit_command_detected else '❌'}")

        if continuous_mode_detected and new_task_prompt_detected:
            print("\n🎉 连续任务模式测试通过！")
            return True
        else:
            print("\n❌ 连续任务模式测试失败")
            return False

    except KeyboardInterrupt:
        print("\n⚡ 用户中断测试")
        process.terminate()
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    exit(0 if success else 1)