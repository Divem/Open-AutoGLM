#!/usr/bin/env python3
"""
测试截图数据提取功能
"""

import requests
import json

def test_api_response():
    """测试API响应"""
    url = "http://localhost:8080/api/tasks/test/report"

    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("API响应成功:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("API响应失败:")
            print(response.text)

    except Exception as e:
        print(f"请求失败: {e}")

def test_screenshot_files():
    """测试截图文件"""
    import os

    screenshots_dir = "/Users/dawinyuan/Documents/coder/Open-AutoGLM/web/static/screenshots"

    if os.path.exists(screenshots_dir):
        files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
        print(f"找到 {len(files)} 个截图文件:")
        for i, file in enumerate(files[:5]):  # 只显示前5个
            print(f"  {i+1}. {file}")
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
    else:
        print("截图目录不存在")

if __name__ == "__main__":
    print("=== 测试截图数据提取 ===")

    print("\n1. 测试截图文件:")
    test_screenshot_files()

    print("\n2. 测试API响应:")
    test_api_response()