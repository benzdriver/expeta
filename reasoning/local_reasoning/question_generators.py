"""
局部推理问题生成模块。
根据不同的推理目标，生成针对性的问题，引导思考过程。
"""

from typing import Dict, List, Any
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re

from llm_services.executor import run_prompt

async def generate_questions(
    entity_name: str,
    entity_data: Dict[str, Any],
    context: str = None,
    round_num: int = 1
) -> List[str]:
    """
    为测试生成问题的简化版函数。
    
    Args:
        entity_name: 实体名称
        entity_data: 实体数据
        context: 上下文信息（可选）
        round_num: 当前轮次序号（默认为1）
        
    Returns:
        List[str]: 生成的问题列表
    """
    # 使用深度架构精细化作为默认目标
    round_goal = "深度架构精细化"
    
    # 如果没有提供上下文，使用实体数据作为上下文
    if context is None:
        context = f"""
实体名称: {entity_name}

实体摘要:
{json.dumps(entity_data, indent=2, ensure_ascii=False)}
"""
    
    # 调用完整版问题生成函数
    return await generate_questions_for_round(
        entity_name=entity_name,
        round_goal=round_goal,
        round_num=round_num,
        context=context
    )

async def generate_questions_for_round(
    entity_name: str,
    round_goal: str,
    round_num: int,
    context: str,
    num_questions: int = 5
) -> List[str]:
    """
    为特定推理轮次生成问题。
    
    Args:
        entity_name: 实体名称
        round_goal: 当前轮次目标
        round_num: 当前轮次序号
        context: 上下文信息
        num_questions: 生成问题数量
        
    Returns:
        List[str]: 生成的问题列表
    """
    # 根据目标选择合适的问题生成器
    if round_goal == "上下文理解与基础架构识别":
        return await generate_context_understanding_questions(entity_name, context, num_questions)
    elif round_goal == "架构模式与最佳实践应用":
        return await generate_architecture_pattern_questions(entity_name, context, num_questions)
    elif round_goal == "一致性检查与冲突解决":
        return await generate_consistency_check_questions(entity_name, context, num_questions)
    elif round_goal == "深度架构精细化":
        return await generate_deep_architecture_questions(entity_name, context, num_questions)
    else:
        # 默认问题生成器
        return await generate_default_questions(entity_name, round_goal, context, num_questions)

async def generate_context_understanding_questions(entity_name: str, context: str, num_questions: int) -> List[str]:
    """生成上下文理解与基础架构识别阶段的问题"""
    prompt = f"""我需要针对软件模块 "{entity_name}" 生成 {num_questions} 个深入的问题，用于理解其基础架构和上下文。
    
### 上下文信息：
{context}

### 问题要求：
1. 问题应聚焦于识别模块的核心功能和职责
2. 探索模块的边界和与其他模块的关系
3. 明确适合该模块的基本架构风格和技术选型
4. 识别关键用户场景和流程
5. 帮助定义模块的核心数据实体和状态管理需求

请生成 {num_questions} 个深入的、能引导架构思考的问题。每个问题应当独立存在，并且格式为：问题内容。
不要输出问题编号或任何额外文字。
"""
    
    return await parse_questions_from_llm_response(prompt)

async def generate_architecture_pattern_questions(entity_name: str, context: str, num_questions: int) -> List[str]:
    """生成架构模式与最佳实践应用阶段的问题"""
    prompt = f"""我需要针对软件模块 "{entity_name}" 生成 {num_questions} 个关于架构模式与最佳实践应用的深入问题。

### 上下文信息：
{context}

### 问题要求：
1. 问题应聚焦于确定适合该模块的架构模式和设计模式
2. 探索各组件间的交互和通信方式
3. 考虑数据流设计和状态管理策略
4. 明确API和接口设计的最佳实践
5. 帮助确定技术实现细节和库/框架选择

请生成 {num_questions} 个深入的、能引导架构思考的问题。每个问题应当独立存在，并且格式为：问题内容。
不要输出问题编号或任何额外文字。
"""
    
    return await parse_questions_from_llm_response(prompt)

async def generate_consistency_check_questions(entity_name: str, context: str, num_questions: int) -> List[str]:
    """生成一致性检查与冲突解决阶段的问题"""
    prompt = f"""我需要针对软件模块 "{entity_name}" 生成 {num_questions} 个关于架构一致性检查和冲突解决的深入问题。

### 上下文信息：
{context}

### 问题要求：
1. 问题应聚焦于检查模块与全局架构约束的一致性
2. 验证与相关模块的接口兼容性
3. 识别和解决循环依赖和架构分层违反问题
4. 分析当前依赖关系是否合理，以及如何优化依赖结构
5. 探索潜在的架构冲突和风险点
6. 确保模块职责边界清晰，避免职责重叠
7. 评估依赖方向是否符合系统层次结构（上层依赖下层）
8. 确保命名、编码规范和最佳实践的遵循

请生成 {num_questions} 个深入的、能引导架构思考的问题。每个问题应当独立存在，并且格式为：问题内容。
不要输出问题编号或任何额外文字。
"""
    
    return await parse_questions_from_llm_response(prompt)

async def generate_deep_architecture_questions(entity_name: str, context: str, num_questions: int) -> List[str]:
    """生成深度架构精细化阶段的问题"""
    prompt = f"""我需要针对软件模块 "{entity_name}" 生成 {num_questions} 个关于深度架构精细化的深入问题。

### 上下文信息：
{context}

### 问题要求：
1. 问题应聚焦于细化接口规范和参数定义
2. 探索错误处理和异常流程设计
3. 考虑非功能性需求（性能、安全性、可扩展性）实现
4. 规划扩展点和未来演进的可能性
5. 思考测试策略和质量保证方法

请生成 {num_questions} 个深入的、能引导架构思考的问题。每个问题应当独立存在，并且格式为：问题内容。
不要输出问题编号或任何额外文字。
"""
    
    return await parse_questions_from_llm_response(prompt)

async def generate_default_questions(entity_name: str, round_goal: str, context: str, num_questions: int) -> List[str]:
    """生成默认问题集"""
    prompt = f"""我需要针对软件模块 "{entity_name}" 在 "{round_goal}" 阶段生成 {num_questions} 个深入的架构分析问题。

### 上下文信息：
{context}

### 问题要求：
1. 问题应当关注架构设计的核心方面
2. 探索该模块的功能、职责和实现方式
3. 考虑与其他组件的交互和接口设计
4. 思考可能存在的架构风险和优化方向
5. 帮助完善关键设计决策的理由

请生成 {num_questions} 个深入的、能引导架构思考的问题。每个问题应当独立存在，并且格式为：问题内容。
不要输出问题编号或任何额外文字。
"""
    
    return await parse_questions_from_llm_response(prompt)

async def parse_questions_from_llm_response(prompt: str) -> List[str]:
    """从LLM响应中解析问题列表"""
    response = await run_prompt(
        system_message="""你是一个专业的软件架构师，擅长提出深入的、有价值的架构分析问题。
请按照要求生成架构推理问题，每个问题应该独立成行，不要带有编号或额外说明。
问题应该直接、明确，且针对性强，能够引导深度架构思考。""",
        user_message=prompt
    )
    
    # 分割成行，清理空行和多余空格
    questions = []
    for line in response.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('注：'):
            # 移除问题编号（如"1. "，"Q1："等）
            line = re.sub(r'^[0-9]+[\.\)、:]?\s*', '', line)
            line = re.sub(r'^Q[0-9]+[\.\)、:]?\s*', '', line)
            questions.append(line)
    
    return questions 