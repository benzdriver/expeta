from typing import List, Optional, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import JSONOutputParser
from langchain.prompts import ChatPromptTemplate

from llm_v2.client_factory import get_chat_client

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
    output_parser = JSONOutputParser() if return_json else StrOutputParser()
    
    # 构建并执行链
    chain = prompt | llm | output_parser
    
    try:
        # 执行链并返回结果
        return await chain.ainvoke({})
    except Exception as e:
        error_msg = f"LLM 调用失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "status": "error",
            "exception": str(e)
        } 