"""
局部推理答案生成模块。
生成对架构问题的深入分析和回答，提供架构决策和理由。
"""

from typing import Dict, List, Any
from llm_services.executor import run_prompt

async def generate_answer(
    entity_name: str,
    question: str,
    context: str,
    round_goal: str
) -> str:
    """
    生成对特定架构问题的回答。
    
    Args:
        entity_name: 实体名称
        question: 问题内容
        context: 上下文信息
        round_goal: 当前推理目标
        
    Returns:
        str: 生成的答案
    """
    # 根据不同轮次的目标，调整系统提示
    system_prompt = get_system_prompt_for_round(round_goal)
    
    # 构建用户提示
    user_prompt = f"""作为专业软件架构师，请回答关于 "{entity_name}" 模块的以下架构问题：

问题：{question}

请基于以下信息提供深入、系统的分析和回答：

{context}

回答时请：
1. 提供明确的架构决策和建议
2. 分析多种可能的设计选择
3. 说明决策理由和权衡考量
4. 结合行业最佳实践和设计模式
5. 考虑实际技术和业务约束

请直接开始你的回答，无需重复问题。"""

    # 调用LLM生成回答
    answer = await run_prompt(
        system_message=system_prompt,
        user_message=user_prompt
    )
    
    return answer

def get_system_prompt_for_round(round_goal: str) -> str:
    """根据推理轮次目标获取系统提示"""
    
    base_prompt = """你是一个专业的软件架构师，在进行深度架构推理过程中，你需要思考软件架构的各个层面。

你的思考模式：
1. 结构思考 - 考虑系统的层次结构、模块划分和组件关系
2. 行为思考 - 分析数据流动方式、通信模式和控制流程
3. 模式思考 - 应用适当的架构模式和设计模式解决特定问题
4. 质量思考 - 评估架构如何满足非功能性需求（性能、安全性、可维护性等）
5. 演进思考 - 考虑架构如何支持系统未来的扩展和变化"""
    
    # 根据轮次目标添加特定指导
    if round_goal == "上下文理解与基础架构识别":
        return base_prompt + """

针对上下文理解与基础架构识别，你应该：
- 分析需求和用例，提取架构关键点
- 识别核心功能和职责边界
- 确定适合的整体架构风格
- 定义关键的技术约束和限制
- 明确主要的业务实体和数据流
"""
    
    elif round_goal == "架构模式与最佳实践应用":
        return base_prompt + """

针对架构模式与最佳实践应用，你应该：
- 推荐适合的架构模式和设计模式
- 设计组件间的交互和依赖关系
- 规划模块的内部结构和分层
- 定义清晰的API和接口设计
- 选择适当的技术栈和实现方案
"""
    
    elif round_goal == "一致性检查与冲突解决":
        return base_prompt + """

针对一致性检查与冲突解决，你应该：
- 检查架构设计与全局约束的一致性
- 验证组件间接口的兼容性
- 识别潜在的职责重叠和循环依赖
- 解决不同设计目标间的冲突
- 评估当前设计与最佳实践的符合度
"""
    
    elif round_goal == "深度架构精细化":
        return base_prompt + """

针对深度架构精细化，你应该：
- 详细定义每个接口和组件的具体实现
- 设计完善的错误处理和异常流程
- 优化性能、安全性和可扩展性
- 规划版本演进和兼容性策略
- 确定测试和部署的关键考量
"""
    
    else:
        # 默认系统提示
        return base_prompt 

async def generate_answers(
    questions: List[str],
    context: str,
    entity_name: str = "当前实体",
    round_goal: str = "深度架构精细化"
) -> List[str]:
    """
    批量生成多个问题的答案。
    
    Args:
        questions: 问题列表
        context: 上下文信息
        entity_name: 实体名称（默认值）
        round_goal: 当前推理目标（默认值）
        
    Returns:
        List[str]: 答案列表
    """
    answers = []
    
    # 如果问题列表为空，返回空列表
    if not questions:
        return []
    
    # 为每个问题生成答案
    for question in questions:
        answer = await generate_answer(
            entity_name=entity_name,
            question=question,
            context=context,
            round_goal=round_goal
        )
        answers.append(answer)
    
    return answers 