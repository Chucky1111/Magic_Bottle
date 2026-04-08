#!/usr/bin/env python3
"""
简单调试 - 检查思考模式配置问题
"""

import sys
sys.path.append('.')

print("=== 简单配置调试 ===")

from config.settings import settings

print("1. 全局配置:")
print(f"   settings.enable_thinking: {settings.enable_thinking}")

print("\n2. writer_llm 配置:")
print(f"   settings.writer_llm.enable_thinking: {settings.writer_llm.enable_thinking}")

print("\n3. 获取client配置:")
config = settings.writer_llm.get_client_config()
print(f"   config keys: {list(config.keys())}")
print(f"   config.enable_thinking: {config.get('enable_thinking', 'NOT FOUND')}")
print(f"   config.extra_body: {config.get('extra_body', 'NOT FOUND')}")

print("\n4. 环境变量检查:")
import os
print(f"   LLM__ENABLE_THINKING: {os.getenv('LLM__ENABLE_THINKING')}")
print(f"   WRITER_LLM__ENABLE_THINKING: {os.getenv('WRITER_LLM__ENABLE_THINKING')}")

print("\n=== 建议 ===")
if not config.get('extra_body'):
    print("问题：writer_llm配置中没有extra_body字段")
    print("解决方案：在.env中添加 WRITER_LLM__ENABLE_THINKING=true")
else:
    print("配置正确，问题可能在其他地方")