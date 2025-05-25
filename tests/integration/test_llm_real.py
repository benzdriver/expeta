from common import print_log
"""
LLM服务模块集成测试（真实API调用）
该测试文件针对llm_services模块进行真实API调用（不使用mock），测试与OpenAI等LLM服务的集成
"""

import os
import json
import pytest
from pathlib import Path

# 导入LLM服务模块
from llm_services.executor import run_prompt
from llm_services.chat import chat
from llm_services.client_factory import get_chat_client

@pytest.mark.asyncio
async def test_real_run_prompt():
    """测试LLM执行器真实功能"""
    
    # 准备测试数据
    system_message = "你是一个专业的软件架构师，擅长解释技术概念。"
    user_message = "请简要解释什么是微服务架构及其主要优缺点。"
    
    # 不使用mock，直接调用实际函数
    response = await run_prompt(
        system_message=system_message,
        user_message=user_message
    )
    
    # 验证结果
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 100  # 确保回答有足够长度
    
    # 打印结果，方便debug
    print("LLM回答:", response[:300] + "..." if len(response) > 300 else response)

@pytest.mark.asyncio
async def test_real_run_prompt_with_json():
    """测试LLM执行器返回JSON功能"""
    
    # 准备测试数据
    system_message = "你是一个专业的软件架构师，擅长提供结构化的分析。"
    user_message = """分析微服务架构的主要特点，并以JSON格式返回结果。
    包括以下字段：特点(features)、优点(advantages)、缺点(disadvantages)。
    每个字段都应该是一个字符串数组。"""
    
    # 定义一个自定义解析函数
    def json_parser(text):
        """解析JSON响应"""
        import json
        import re
        
        # 尝试从文本中提取JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        # 尝试直接解析文本
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "无法解析JSON", "text": text}
    
    # 不使用mock，直接调用实际函数
    response = await run_prompt(
        system_message=system_message,
        user_message=user_message,
        parse_response=json_parser
    )
    
    # 验证结果
    assert response is not None
    
    # 根据返回类型验证
    if isinstance(response, dict) and not "error" in response:
        assert "features" in response
        assert "advantages" in response
        assert "disadvantages" in response
        assert isinstance(response["features"], list)
    else:
        # 如果解析失败，打印原始文本
        print("解析JSON失败，原始响应:", response)
        if isinstance(response, dict) and "text" in response:
            assert len(response["text"]) > 50
    
    # 打印结果，方便debug
    if isinstance(response, dict):
        print("LLM JSON回答:", json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print("LLM回答:", response)

@pytest.mark.asyncio
async def test_real_chat():
    """测试LLM聊天功能"""
    
    # 准备测试数据
    system_message = "你是一个专业的软件开发顾问。"
    user_message = "我想开发一个移动应用，应该选择React Native还是Flutter？"
    
    # 不使用mock，直接调用实际函数
    response = await chat(
        system_message=system_message,
        user_message=user_message,
        model="gpt-3.5-turbo"  # 使用经济型模型
    )
    
    # 验证结果
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 100  # 确保回答有足够长度
    
    # 打印结果，方便debug
    print("LLM聊天回答:", response[:300] + "..." if len(response) > 300 else response)

@pytest.mark.asyncio
async def test_real_chat_with_messages():
    """测试使用消息列表的LLM聊天功能"""
    
    # 准备测试数据
    messages = [
        {"role": "system", "content": "你是一个专业的软件开发顾问。"},
        {"role": "user", "content": "我想开发一个移动应用，应该选择React Native还是Flutter？"},
    ]
    
    # 不使用mock，直接调用实际函数
    response = await chat(
        messages=messages,
        model="gpt-3.5-turbo"  # 使用经济型模型
    )
    
    # 验证结果
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 100  # 确保回答有足够长度
    
    # 打印结果，方便debug
    print("LLM聊天回答(使用消息列表):", response[:300] + "..." if len(response) > 300 else response)

@pytest.mark.asyncio
async def test_real_get_chat_client():
    """测试获取LLM客户端功能"""
    
    # 不使用mock，直接调用实际函数
    client = get_chat_client("gpt-3.5-turbo")
    
    # 验证结果
    assert client is not None
    
    # 测试客户端类型
    from langchain_openai import ChatOpenAI
    assert isinstance(client, ChatOpenAI)

@pytest.mark.asyncio
async def test_real_run_prompt_with_specific_model():
    """测试使用特定模型的LLM执行器功能"""
    
    # 准备测试数据
    system_message = "你是一个简洁明了的技术顾问。"
    user_message = "什么是Docker容器？请用一句话回答。"
    
    # 不使用mock，直接调用实际函数，使用经济型模型
    response = await run_prompt(
        system_message=system_message,
        user_message=user_message,
        model="gpt-3.5-turbo"  # 指定使用经济型模型
    )
    
    # 验证结果
    assert response is not None
    assert isinstance(response, str)
    
    # 打印结果，方便debug
    print("经济型模型回答:", response)
    
    # 如果可能，同时测试高级模型
    try:
        advanced_response = await run_prompt(
            system_message=system_message,
            user_message=user_message,
            model="gpt-4"  # 尝试使用高级模型
        )
        
        # 验证结果
        assert advanced_response is not None
        assert isinstance(advanced_response, str)
        
        print("高级模型回答:", advanced_response)
    except Exception as e:
        print_log(f"高级模型测试跳过: {e}")

@pytest.mark.asyncio
async def test_real_run_prompt_with_structured_output():
    """测试LLM结构化输出功能"""
    
    # 准备测试数据
    system_message = "你是一个数据分析专家，擅长提供结构化信息。"
    user_message = """分析以下移民申请类型，并以结构化格式返回每种类型的主要特点:
    - 联邦技术移民
    - 省提名计划
    - 创业移民
    - 家庭团聚
    
    对每种类型，请提供以下几点信息：
    1. 申请条件
    2. 申请流程
    3. 处理时间
    4. 主要优势
    5. 适合人群
    """
    
    # 定义输出解析函数
    def parse_immigration_types(text):
        """解析移民类型信息"""
        import re
        
        # 先打印原始文本以便调试
        print("LLM原始回答:", text[:500] + "..." if len(text) > 500 else text)
        
        # 改进的解析逻辑
        types = {}
        current_type = None
        current_feature = None
        
        # 尝试不同的模式匹配
        # 模式1：新的移民类型标题（可能是粗体、标题格式或列表项）
        type_pattern = r'(?:^|\n)(?:\*\*|\#\#\s*|[*\-•]?\s*)?(联邦技术移民|省提名计划|创业移民|家庭团聚)(?:[：:]*|\*\*|\n)'
        
        # 模式2：特征分类（可能是粗体或数字列表）
        feature_pattern = r'(?:^|\n)(?:\*\*|\d+\.\s*|\*\s*)(申请条件|申请流程|处理时间|主要优势|适合人群)(?:[：:]*|\*\*)'
        
        # 遍历每一行
        for line in text.split('\n'):
            # 检查是否是新的移民类型
            type_match = re.search(type_pattern, line)
            if type_match:
                current_type = type_match.group(1)
                if current_type not in types:
                    types[current_type] = {}
                continue
                
            # 检查是否是特征分类
            feature_match = re.search(feature_pattern, line)
            if feature_match and current_type:
                current_feature = feature_match.group(1)
                if current_feature not in types[current_type]:
                    types[current_type][current_feature] = []
                continue
                
            # 添加特征内容，排除空行和分隔符
            if current_type and current_feature and line.strip() and not re.match(r'^[-_*=#]+$', line.strip()):
                # 移除行首的列表标记符号
                clean_line = re.sub(r'^[*\-•]\s*', '', line.strip())
                if clean_line and not re.match(r'^(?:\*\*|\d+\.\s*|\*\s*)', clean_line):
                    types[current_type][current_feature].append(clean_line)
        
        # 如果解析失败，尝试简单的分段提取
        if not types or all(len(v) == 0 for v in types.values()):
            sections = re.split(r'\n\s*(?=\*\*|\d+\.)|\n\s*\n', text)
            current_type = None
            
            for section in sections:
                for imm_type in ["联邦技术移民", "省提名计划", "创业移民", "家庭团聚"]:
                    if imm_type in section:
                        current_type = imm_type
                        if current_type not in types:
                            types[current_type] = {"特点": []}
                        
                        # 提取该部分的要点
                        points = re.findall(r'[*\-•]?\s*(.+)', section)
                        for point in points:
                            if point.strip() and imm_type not in point:
                                types[current_type]["特点"].append(point.strip())
        
        return types
    
    # 不使用mock，直接调用实际函数
    response = await run_prompt(
        system_message=system_message,
        user_message=user_message,
        parse_response=parse_immigration_types
    )
    
    # 验证结果
    assert response is not None
    
    # 结果可能是字典（成功解析）或字符串（解析失败但返回原文）
    if isinstance(response, dict):
        assert len(response) > 0
        # 只需检查字典是否非空，内容由模型生成，可能变化
        print("结构化输出:", json.dumps(response, indent=2, ensure_ascii=False))
    else:
        # 如果是字符串，确保有内容
        assert isinstance(response, str)
        assert len(response) > 50
        print("未能解析为结构化数据，原始文本:", response[:200]) 