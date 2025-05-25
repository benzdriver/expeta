from common import print_log
from typing import List, Optional, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from llm_services.client_factory import get_chat_client

async def chat(
    system_message: Optional[str] = None,
    user_message: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    model: str = "gpt-4",
    temperature: float = 0.0,
    return_json: bool = False
) -> Any:
    """
    基于 LangChain 的统一聊天接口
    
    支持三种调用方式：
    1. messages: 直接传完整历史
    2. system_message + user_message: 组装 system+user
    3. user_message: 单轮 user 消息
    """
    # 获取 LLM 客户端
    llm = get_chat_client(model_name=model, temperature=temperature)
    
    # 构建消息列表
    if messages:
        chat_messages = [
            SystemMessage(content=msg["content"]) if msg["role"] == "system"
            else HumanMessage(content=msg["content"]) if msg["role"] == "user"
            else AIMessage(content=msg["content"])
            for msg in messages
        ]
    elif system_message and user_message:
        chat_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
    elif user_message:
        chat_messages = [HumanMessage(content=user_message)]
    else:
        raise ValueError("必须提供 messages、(system_message, user_message) 或 user_message 中的一种")

    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages(chat_messages)
    
    # 选择输出解析器
    output_parser = JsonOutputParser() if return_json else StrOutputParser()
    
    # 构建并执行链
    chain = prompt | llm | output_parser
    
    try:
        # 执行链并返回结果
        return await chain.ainvoke({})
    except Exception as e:
        error_msg = f"LLM 调用失败: {str(e)}"
        print_log(f"{error_msg}", level="error")
        return {
            "error": error_msg,
            "status": "error",
            "exception": str(e)
        }

# 为兼容测试添加chat_completion函数
async def chat_completion(
    system_message: Optional[str] = None,
    user_message: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    model: str = "gpt-4",
    temperature: float = 0.0,
    response_format: Optional[str] = None,
    stream: bool = False
) -> Any:
    """
    兼容测试的简化版聊天接口
    
    Args:
        system_message: 系统消息
        user_message: 用户消息
        messages: 完整消息历史
        model: 模型名称
        temperature: 温度参数
        response_format: 响应格式
        stream: 是否流式输出
        
    Returns:
        Any: 聊天完成结果
    """
    # 转换参数调用新的chat函数
    return_json = response_format == "json"
    
    result = await chat(
        system_message=system_message,
        user_message=user_message,
        messages=messages,
        model=model,
        temperature=temperature,
        return_json=return_json
    )
    
    # 如果是流式输出(测试中不实际实现)
    if stream:
        async def mock_stream():
            yield result
        return mock_stream()
        
    return result 