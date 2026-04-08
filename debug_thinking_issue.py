#!/usr/bin/env python3
"""
诊断DeepSeek思考模式问题
检查配置、API连接和实际调用
"""

import sys
import os
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append('.')

def test_config():
    """测试配置"""
    print("=== 配置测试 ===")
    
    from config.settings import settings
    
    print(f"1. enable_thinking: {settings.enable_thinking} (type: {type(settings.enable_thinking)})")
    print(f"2. writer_llm config keys: {list(settings.writer_llm.get_client_config().keys())}")
    
    config = settings.writer_llm.get_client_config()
    print(f"3. writer_llm extra_body: {config.get('extra_body')}")
    print(f"4. writer_llm enable_thinking: {config.get('enable_thinking')}")
    
    return config

def test_llm_client():
    """测试LLM客户端"""
    print("\n=== LLM客户端测试 ===")
    
    from core.llm import LLMClient
    from config.settings import settings
    
    config = settings.writer_llm.get_client_config()
    print(f"1. 使用配置创建客户端: {config.get('model')}")
    
    client = LLMClient(config=config)
    print(f"2. 客户端属性:")
    print(f"   enable_thinking: {client.enable_thinking}")
    print(f"   extra_body: {client.extra_body}")
    print(f"   model: {client.model}")
    print(f"   base_url: {client.base_url}")
    
    return client

def test_api_call(client):
    """测试API调用"""
    print("\n=== API调用测试 ===")
    
    # 简单消息
    messages = [
        {"role": "user", "content": "请简单回答：你好，这是一次测试。"}
    ]
    
    print("1. 测试简单调用（无extra_body覆盖）...")
    try:
        response = client.chat(messages)
        print(f"   成功！响应长度: {len(response)} 字符")
        print(f"   响应预览: {response[:100]}...")
        return True
    except Exception as e:
        print(f"   失败！错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_with_explicit_thinking(client):
    """测试显式思考模式调用"""
    print("\n=== 显式思考模式测试 ===")
    
    messages = [
        {"role": "user", "content": "请思考并回答：1+1等于多少？"}
    ]
    
    print("1. 使用extra_body参数调用...")
    try:
        response = client.chat(messages, extra_body={"thinking": {"type": "enabled"}})
        print(f"   成功！响应长度: {len(response)} 字符")
        print(f"   响应预览: {response[:100]}...")
        return True
    except Exception as e:
        print(f"   失败！错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_timeout():
    """检查超时设置"""
    print("\n=== 超时设置检查 ===")
    
    from config.settings import settings
    
    config = settings.writer_llm.get_client_config()
    timeout = config.get('timeout', 120)
    print(f"1. 当前超时设置: {timeout}秒")
    print(f"2. 是否启用思考模式: {settings.enable_thinking}")
    
    # 建议
    if settings.enable_thinking and timeout < 180:
        print(f"3. [警告]：思考模式可能需要更长时间，建议增加超时到180秒以上")
    else:
        print(f"3. 超时设置看起来合适")

def simulate_workflow_call():
    """模拟工作流调用"""
    print("\n=== 模拟工作流调用 ===")
    
    from core.llm import LLMClient
    from config.settings import settings
    
    # 使用writer配置
    config = settings.writer_llm.get_client_config()
    client = LLMClient(config=config)
    
    # 模拟design阶段的提示词
    messages = [
        {"role": "system", "content": "你是一个小说创作助手。"},
        {"role": "user", "content": "请设计第一章的大纲。"}
    ]
    
    print("1. 模拟design阶段调用...")
    print(f"   使用模型: {client.model}")
    print(f"   extra_body: {client.extra_body}")
    print(f"   消息数量: {len(messages)}")
    
    try:
        # 设置较短的超时用于测试
        import openai
        original_timeout = openai.DEFAULT_TIMEOUT if hasattr(openai, 'DEFAULT_TIMEOUT') else None
        
        response = client.chat(messages, timeout=30)  # 30秒测试超时
        print(f"   成功！获得响应")
        print(f"   响应前200字符: {response[:200]}...")
        return True
    except Exception as e:
        print(f"   失败！错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")
        
        # 检查特定错误
        if "timeout" in str(e).lower():
            print("   ⚠️ 超时错误：思考模式可能需要更长时间")
        elif "rate limit" in str(e).lower():
            print("   ⚠️ 速率限制错误")
        elif "invalid request" in str(e).lower():
            print("   ⚠️ 无效请求：extra_body参数可能有问题")
        
        import traceback
        traceback.print_exc()
        return False

def main():
    """主诊断函数"""
    print("DeepSeek思考模式问题诊断")
    print("=" * 60)
    
    # 检查配置
    config = test_config()
    
    # 检查超时
    check_timeout()
    
    # 测试客户端
    client = test_llm_client()
    
    # 测试简单API调用
    simple_success = test_api_call(client)
    
    # 测试思考模式调用
    thinking_success = test_api_with_explicit_thinking(client)
    
    # 模拟工作流调用
    workflow_success = simulate_workflow_call()
    
    print("\n" + "=" * 60)
    print("诊断结果汇总:")
    print(f"1. 配置检查: {'通过' if config else '失败'}")
    print(f"2. 简单API调用: {'成功' if simple_success else '失败'}")
    print(f"3. 思考模式调用: {'成功' if thinking_success else '失败'}")
    print(f"4. 工作流模拟: {'成功' if workflow_success else '失败'}")
    
    if not simple_success:
        print("\n⚠️ 问题：即使简单调用也失败，可能是API密钥或网络问题")
    elif simple_success and not thinking_success:
        print("\n⚠️ 问题：思考模式调用失败但普通调用成功，说明思考模式参数有问题")
    elif simple_success and thinking_success and not workflow_success:
        print("\n⚠️ 问题：工作流模拟失败但直接调用成功，可能是提示词或上下文问题")
    elif all([simple_success, thinking_success, workflow_success]):
        print("\n✅ 所有测试通过！问题可能在其他地方")
    
    print("\n建议:")
    print("1. 检查.env中的LLM__ENABLE_THINKING设置")
    print("2. 检查API密钥是否有效")
    print("3. 尝试增加超时时间（在config中设置）")
    print("4. 查看data/debug.log获取详细错误信息")

if __name__ == "__main__":
    main()