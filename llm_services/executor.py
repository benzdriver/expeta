from common import print_log
from typing import Any, Callable, Optional, List
from langchain.text_splitter import TokenTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm_services.client_factory import get_chat_client  # 更新导入路径

async def run_prompt(
    *,
    user_message: Optional[str] = None,
    system_message: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    model: str = "gpt-4",
    max_input_tokens: int = 8000,
    parse_response: Callable[[str], Any] = lambda x: x,
    merge_result: Callable[[Any, Any], Any] = lambda acc, x: x,
    get_system_prompt: Optional[Callable[[int, int], str]] = None,
    return_json: bool = False
) -> Any:
    """
    基于 LangChain 的统一 LLM 执行器
    
    特点：
    1. 自动处理长文本分块
    2. 支持自定义响应解析
    3. 支持结果合并
    4. 支持 JSON 输出
    """
    # 获取 LLM 客户端
    llm = get_chat_client(model_name=model)
    
    # 设置文本分割器
    text_splitter = TokenTextSplitter(
        model_name=model,
        chunk_size=max_input_tokens,
        chunk_overlap=200
    )
    
    # 分割输入文本
    if user_message:
        chunks = text_splitter.split_text(user_message)
    else:
        chunks = [""]  # 空文本情况
        
    print_log(f"📄 文本已分割为 {len(chunks)} 个块")
    
    # 使用字符串输出解析器
    output_parser = StrOutputParser()
    
    # 处理每个文本块
    accumulated_result = None
    for i, chunk in enumerate(chunks):
        try:
            # 获取当前块的 system prompt
            current_system = get_system_prompt(i + 1, len(chunks)) if get_system_prompt else system_message
            
            # 创建提示模板
            prompt = PromptTemplate.from_template(
                "{system}\n\n{user}" if current_system else "{user}"
            )
            
            # 构建链
            chain = (
                prompt | 
                llm | 
                output_parser | 
                parse_response
            )
            
            # 执行链
            result = await chain.ainvoke({
                "system": current_system,
                "user": chunk
            })
            
            # 合并结果
            accumulated_result = merge_result(accumulated_result, result)
            
        except Exception as e:
            print_log(f"处理块 {i+1}/{len(chunks)} 时出错: {str(e)}", level="error")
            continue
    
    return accumulated_result 