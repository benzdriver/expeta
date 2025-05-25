from common import print_log
"""
局部推理链模块。
整合上下文构建、问题生成、回答生成和摘要更新，形成完整的局部推理流程。
"""

from typing import Dict, List, Any, Optional, Tuple
import json

from knowledge.reasoning_memory import store_reasoning, extract_decisions_from_qa
from reasoning.local_reasoning.context_builder import build_local_reasoning_context
from reasoning.local_reasoning.question_generators import generate_questions_for_round
from reasoning.local_reasoning.answer_generators import generate_answer, generate_answers
from reasoning.local_reasoning.summary_updaters import update_entity_summary

async def run_local_reasoning_round(
    entity_name: str,
    current_summary: Dict[str, Any],
    round_num: int,
    round_goal: str,
    previous_qa: List[Dict[str, str]] = None,
    global_constraints: Optional[Dict[str, Any]] = None,
    num_questions: int = 5
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    运行单轮局部推理。
    
    Args:
        entity_name: 实体名称
        current_summary: 当前实体摘要
        round_num: 当前轮次序号
        round_goal: 当前轮次目标
        previous_qa: 之前轮次的问答历史
        global_constraints: 全局架构约束
        num_questions: 生成问题数量
        
    Returns:
        Tuple[Dict[str, Any], List[Dict[str, str]]]: (更新后的摘要, 当前轮次问答)
    """
    if previous_qa is None:
        previous_qa = []
        
    print_log(f"🔄 开始 {entity_name} 的第 {round_num} 轮推理: {round_goal}")
    
    # 1. 构建上下文
    context = await build_local_reasoning_context(
        entity_name=entity_name,
        round_num=round_num,
        round_goal=round_goal,
        current_summary=current_summary,
        previous_qa=previous_qa,
        global_constraints=global_constraints
    )
    
    # 2. 生成问题
    print_log(f"🔄 生成问题 (轮次 {round_num}/{num_questions}): {round_goal}")
    questions = await generate_questions_for_round(
        entity_name=entity_name,
        round_goal=round_goal,
        round_num=round_num,
        context=context,
        num_questions=num_questions
    )
    
    print_log(f"生成了 {len(questions)} 个问题", level="info")
    
    # 3. 回答问题
    round_qa = []
    for i, question in enumerate(questions):
        print_log(f"🤔 问题 {i+1}/{len(questions)}: {question[:50]}...")
        
        answer = await generate_answer(
            entity_name=entity_name,
            question=question,
            context=context,
            round_goal=round_goal
        )
        
        round_qa.append({"question": question, "answer": answer})
    
    # 4. 更新摘要并验证依赖关系
    updated_summary = await update_entity_summary(
        entity_name=entity_name,
        current_summary=current_summary,
        qa_history=round_qa,
        context=context,
        round_goal=round_goal
    )
    
    # 记录是否进行了依赖验证
    if "depends_on" in updated_summary and "depends_on" in current_summary:
        if set(updated_summary["depends_on"]) != set(current_summary["depends_on"]):
            print_log(f"模块 {entity_name} 的依赖关系已更新并验证", level="info")
    
    # 5. 提取关键决策并存储推理记录
    decisions = extract_decisions_from_qa(round_qa)
    
    success = store_reasoning(
        entity_name=entity_name,
        reasoning_type="local",
        round_goal=round_goal,
        qa_history=round_qa,
        decisions=decisions,
        metadata={
            "round_num": round_num,
            "summary_before": current_summary,
            "summary_after": updated_summary
        }
    )
    
    if success:
        print_log(f"已存储推理记录，包含 {len(decisions)} 个关键决策", level="info")
    
    return updated_summary, round_qa

async def run_full_local_reasoning(
    entity_name: str,
    initial_summary: Dict[str, Any],
    global_constraints: Optional[Dict[str, Any]] = None,
    max_rounds: int = 4
) -> Dict[str, Any]:
    """
    运行完整的局部推理流程。
    
    Args:
        entity_name: 实体名称
        initial_summary: 初始实体摘要
        global_constraints: 全局架构约束
        max_rounds: 最大推理轮次
        
    Returns:
        Dict[str, Any]: 最终更新的实体摘要
    """
    # 定义推理轮次
    round_goals = [
        "上下文理解与基础架构识别", 
        "架构模式与最佳实践应用", 
        "一致性检查与冲突解决",
        "深度架构精细化"
    ]
    
    # 限制轮次数量
    rounds_to_run = min(max_rounds, len(round_goals))
    
    current_summary = initial_summary
    all_qa_history = []
    
    for round_num in range(1, rounds_to_run + 1):
        current_goal = round_goals[round_num - 1]
        
        # 运行单轮推理
        updated_summary, round_qa = await run_local_reasoning_round(
            entity_name=entity_name,
            current_summary=current_summary,
            round_num=round_num,
            round_goal=current_goal,
            previous_qa=all_qa_history,
            global_constraints=global_constraints
        )
        
        # 更新状态
        current_summary = updated_summary
        all_qa_history.extend(round_qa)
        
        print_log(f"完成第 {round_num} 轮推理: {current_goal}", level="info")
    
    print_log(f"🎉 {entity_name} 的局部推理完成，共进行了 {rounds_to_run} 轮推理")
    return current_summary

# 为兼容测试添加的函数
async def run_local_reasoning(
    entity_name: str,
    entity_summary: Dict[str, Any],
    round_goal: str,
    previous_qa: List[Dict[str, str]] = None,
    global_constraints: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    简化版的局部推理函数(兼容测试用例)
    
    Args:
        entity_name: 实体名称
        entity_summary: 实体摘要
        round_goal: 推理目标
        previous_qa: 之前的问答历史
        global_constraints: 全局约束
        
    Returns:
        Tuple[Dict[str, Any], List[Dict[str, str]]]: (更新后的摘要, 问答历史)
    """
    # 调用完整实现
    return await run_local_reasoning_round(
        entity_name=entity_name,
        current_summary=entity_summary,
        round_num=1,  # 固定为第一轮
        round_goal=round_goal,
        previous_qa=previous_qa,
        global_constraints=global_constraints,
        num_questions=3  # 简化为3个问题
    ) 