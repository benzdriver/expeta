from typing import List, Dict

# 新增：模型token参数映射
MODEL_TOKEN_LIMITS: Dict[str, Dict[str, int]] = {
    "gpt-4o": {"max_tokens": 128_000, "reserved_output": 8_000},
    "gpt-4-turbo": {"max_tokens": 128_000, "reserved_output": 8_000},
    "gpt-4": {"max_tokens": 8_192, "reserved_output": 1_000},
    "gpt-3.5-turbo": {"max_tokens": 16_385, "reserved_output": 1_000},
    # 可根据需要扩展更多模型
}

def get_model_token_config(model: str) -> Dict[str, int]:
    """
    获取指定模型的token参数配置。
    """
    return MODEL_TOKEN_LIMITS.get(model, {"max_tokens": 8_192, "reserved_output": 1_000})


def get_optimal_chunk_size(total_tokens: int, model: str = "gpt-4o") -> int:
    """
    根据总token数和模型，自动计算每块最大token数。
    """
    config = get_model_token_config(model)
    max_input_tokens = config["max_tokens"] - config["reserved_output"]
    if total_tokens <= max_input_tokens:
        return max_input_tokens
    return max_input_tokens

def split_text_by_tokens(text: str, tokenizer, max_tokens: int = 2000) -> List[str]:
    """
    Splits a long text into chunks based on token limits.
    使用批量编码来减少tokenizer.encode的调用次数。

    Args:
        text: The full input string.
        tokenizer: A tiktoken tokenizer instance.
        max_tokens: Maximum number of tokens per chunk.

    Returns:
        A list of string chunks each under the token limit.
    """
    # 先对整个文本进行一次性编码
    try:
        all_tokens = tokenizer.encode(text)
        total_tokens = len(all_tokens)
        
        # 如果总token数小于max_tokens，直接返回原文本
        if total_tokens <= max_tokens:
            return [text]
        
        # 计算需要多少个块
        n_chunks = (total_tokens + max_tokens - 1) // max_tokens
        
        # 将tokens分成大致相等的几块
        chunk_size = total_tokens // n_chunks + 1
        chunks = []
        
        # 使用decode将token块转回文本
        start = 0
        while start < total_tokens:
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = all_tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end
            
        return chunks
        
    except Exception as e:
        print(f"⚠️ Token分割出错，使用简单的字符分割: {str(e)}")
        # 如果tokenizer出错，使用简单的字符分割作为后备方案
        avg_chars_per_token = 4  # 假设平均每个token约4个字符
        char_limit = max_tokens * avg_chars_per_token
        
        # 简单地按字符数分割
        chunks = []
        for i in range(0, len(text), char_limit):
            chunks.append(text[i:i + char_limit])
        
        return chunks
