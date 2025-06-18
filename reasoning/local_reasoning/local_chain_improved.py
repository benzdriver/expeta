"""
改进的局部推理链模块。
实现分阶段、聚焦的推理流程，集成质量控制。
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
from enum import Enum

from common import print_log
from common.quality_validator import QualityValidator, QualityLevel
from knowledge.reasoning_memory import store_reasoning, extract_decisions_from_qa
from reasoning.local_reasoning.context_builder import build_local_reasoning_context
from reasoning.local_reasoning.answer_generators_improved import (
    generate_specific_answer,
    generate_structured_json_summary,
    PHASED_ANSWER_TEMPLATES
)

class ReasoningPhase(Enum):
    """推理阶段枚举"""
    FUNCTION_DEFINITION = "功能定义与边界划分"
    TECHNICAL_IMPLEMENTATION = "技术实现与模式选择"
    INTEGRATION_DESIGN = "集成设计与依赖分析"
    QUALITY_ASSURANCE = "质量保证与优化"

@dataclass
class PhaseConfig:
    """推理阶段配置"""
    phase: ReasoningPhase
    focus_areas: List[str]
    required_outputs: List[str]
    quality_threshold: int = 70
    max_questions: int = 5
    max_retries: int = 2

# 定义各阶段的配置
PHASE_CONFIGS = {
    ReasoningPhase.FUNCTION_DEFINITION: PhaseConfig(
        phase=ReasoningPhase.FUNCTION_DEFINITION,
        focus_areas=["核心功能", "职责边界", "对外接口", "数据模型"],
        required_outputs=["功能列表", "API定义", "数据结构"],
        quality_threshold=75,
        max_questions=5
    ),
    ReasoningPhase.TECHNICAL_IMPLEMENTATION: PhaseConfig(
        phase=ReasoningPhase.TECHNICAL_IMPLEMENTATION,
        focus_areas=["技术栈选择", "设计模式", "架构风格", "关键算法"],
        required_outputs=["技术方案", "类设计", "实现策略"],
        quality_threshold=80,
        max_questions=4
    ),
    ReasoningPhase.INTEGRATION_DESIGN: PhaseConfig(
        phase=ReasoningPhase.INTEGRATION_DESIGN,
        focus_areas=["模块间交互", "依赖关系", "数据流", "接口契约"],
        required_outputs=["依赖图", "接口规范", "集成方案"],
        quality_threshold=75,
        max_questions=4
    ),
    ReasoningPhase.QUALITY_ASSURANCE: PhaseConfig(
        phase=ReasoningPhase.QUALITY_ASSURANCE,
        focus_areas=["性能优化", "安全设计", "测试策略", "监控方案"],
        required_outputs=["性能指标", "安全措施", "测试计划"],
        quality_threshold=70,
        max_questions=3
    )
}

async def generate_focused_questions(
    entity_name: str,
    phase: ReasoningPhase,
    context: str,
    previous_outputs: Dict[str, Any],
    num_questions: int = 5
) -> List[str]:
    """
    生成聚焦的问题，基于当前阶段和之前的输出。
    
    Args:
        entity_name: 实体名称
        phase: 当前推理阶段
        context: 上下文信息
        previous_outputs: 之前阶段的输出
        num_questions: 问题数量
        
    Returns:
        List[str]: 聚焦的问题列表
    """
    config = PHASE_CONFIGS[phase]
    
    # 构建问题生成提示
    system_prompt = f"""你是一个专业的软件架构师，正在进行 {phase.value} 阶段的架构设计。

当前阶段重点：
{chr(10).join(f'- {area}' for area in config.focus_areas)}

需要产出：
{chr(10).join(f'- {output}' for output in config.required_outputs)}

请生成 {num_questions} 个具体、聚焦的问题，引导得出具体的技术方案。

问题要求：
1. 必须与当前阶段重点相关
2. 问题应该引导具体的回答（类名、方法名、技术版本等）
3. 避免开放式或哲学性问题
4. 基于之前的设计决策提出深入问题"""

    # 构建之前输出的摘要
    previous_summary = ""
    if previous_outputs:
        previous_summary = f"\n之前的设计决策：\n{json.dumps(previous_outputs, indent=2, ensure_ascii=False)}\n"
    
    user_prompt = f"""实体名称：{entity_name}

{previous_summary}

基于以下上下文信息，生成 {num_questions} 个聚焦的架构问题：

{context}

请直接列出问题，每行一个，不要编号。"""

    from llm_services.executor import run_prompt
    
    response = await run_prompt(
        system_message=system_prompt,
        user_message=user_prompt,
        temperature=0.7
    )
    
    # 解析问题
    questions = [q.strip() for q in response.strip().split('\n') if q.strip() and not q.strip()[0].isdigit()]
    
    # 确保问题数量
    questions = questions[:num_questions]
    
    # 如果问题不够，添加默认问题
    if len(questions) < num_questions:
        default_questions = {
            ReasoningPhase.FUNCTION_DEFINITION: [
                f"{entity_name} 模块的三个核心功能是什么？请给出具体的功能名称和输入输出。",
                f"{entity_name} 需要暴露哪些RESTful API端点？请给出具体路径和HTTP方法。",
                f"{entity_name} 的核心数据模型包含哪些字段？请给出字段名和类型。"
            ],
            ReasoningPhase.TECHNICAL_IMPLEMENTATION: [
                f"{entity_name} 应该使用什么编程语言和框架？请指定具体版本。",
                f"{entity_name} 需要哪些Service类和Repository类？请给出类名和主要方法。",
                f"{entity_name} 应该采用什么设计模式？请说明具体应用场景。"
            ]
        }
        
        if phase in default_questions:
            questions.extend(default_questions[phase][:num_questions - len(questions)])
    
    return questions[:num_questions]

async def evaluate_and_improve_answer(
    answer: str,
    question: str,
    phase: ReasoningPhase,
    max_retries: int = 2
) -> Tuple[str, QualityReport]:
    """
    评估答案质量并在必要时改进。
    
    Args:
        answer: 原始答案
        question: 问题
        phase: 当前阶段
        max_retries: 最大重试次数
        
    Returns:
        Tuple[str, QualityReport]: (最终答案, 质量报告)
    """
    config = PHASE_CONFIGS[phase]
    
    # 根据阶段确定验证上下文
    context_type = {
        ReasoningPhase.FUNCTION_DEFINITION: "api",
        ReasoningPhase.TECHNICAL_IMPLEMENTATION: "implementation",
        ReasoningPhase.INTEGRATION_DESIGN: "general",
        ReasoningPhase.QUALITY_ASSURANCE: "testing"
    }.get(phase, "general")
    
    best_answer = answer
    best_report = QualityValidator.validate_text(answer, context_type)
    
    # 如果质量不达标，尝试改进
    retry_count = 0
    while best_report.score < config.quality_threshold and retry_count < max_retries:
        retry_count += 1
        print_log(f"答案质量不达标（{best_report.score}分），尝试改进...", level="warning")
        
        # 构建改进提示
        improvement_prompt = f"""之前的回答存在以下问题：
{chr(10).join(best_report.issues)}

改进建议：
{chr(10).join(best_report.suggestions)}

请重新回答，确保提供具体的技术细节。

原始问题：{question}

要求：
1. 必须包含具体的类名、方法名、技术版本
2. 避免使用"处理"、"管理"、"相关"等空泛词汇
3. 提供可执行的示例代码或配置"""

        from llm_services.executor import run_prompt
        
        improved_answer = await run_prompt(
            system_message=PHASED_ANSWER_TEMPLATES.get(phase.value, ""),
            user_message=improvement_prompt,
            temperature=0.2
        )
        
        # 重新评估
        new_report = QualityValidator.validate_text(improved_answer, context_type)
        
        if new_report.score > best_report.score:
            best_answer = improved_answer
            best_report = new_report
    
    return best_answer, best_report

async def run_improved_reasoning_phase(
    entity_name: str,
    phase: ReasoningPhase,
    current_summary: Dict[str, Any],
    previous_phases_output: Dict[str, Any],
    global_constraints: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], float]:
    """
    运行改进的推理阶段。
    
    Args:
        entity_name: 实体名称
        phase: 当前推理阶段
        current_summary: 当前摘要
        previous_phases_output: 之前阶段的输出
        global_constraints: 全局约束
        
    Returns:
        Tuple: (更新的摘要, 问答历史, 平均质量分数)
    """
    config = PHASE_CONFIGS[phase]
    print_log(f"🚀 开始 {entity_name} 的 {phase.value} 阶段")
    
    # 1. 构建聚焦的上下文
    context = await build_local_reasoning_context(
        entity_name=entity_name,
        round_num=list(ReasoningPhase).index(phase) + 1,
        round_goal=phase.value,
        current_summary=current_summary,
        previous_qa=[],
        global_constraints=global_constraints
    )
    
    # 2. 生成聚焦的问题
    questions = await generate_focused_questions(
        entity_name=entity_name,
        phase=phase,
        context=context,
        previous_outputs=previous_phases_output,
        num_questions=config.max_questions
    )
    
    print_log(f"生成了 {len(questions)} 个聚焦问题", level="info")
    
    # 3. 生成高质量答案
    qa_history = []
    quality_scores = []
    
    for i, question in enumerate(questions):
        print_log(f"问题 {i+1}/{len(questions)}: {question}")
        
        # 生成答案
        answer = await generate_specific_answer(
            entity_name=entity_name,
            question=question,
            context=context,
            round_goal=phase.value,
            previous_answers=[qa["answer"] for qa in qa_history]
        )
        
        # 评估和改进答案
        final_answer, quality_report = await evaluate_and_improve_answer(
            answer=answer,
            question=question,
            phase=phase,
            max_retries=config.max_retries
        )
        
        print_log(f"答案质量: {quality_report.score}分 ({quality_report.level.value})", level="info")
        
        qa_history.append({
            "question": question,
            "answer": final_answer,
            "quality_score": quality_report.score,
            "quality_level": quality_report.level.value,
            "quality_issues": quality_report.issues
        })
        
        quality_scores.append(quality_report.score)
    
    # 4. 生成结构化摘要
    updated_summary = await generate_structured_json_summary(
        entity_name=entity_name,
        qa_pairs=qa_history,
        entity_type=current_summary.get("type", "module")
    )
    
    # 5. 验证摘要质量
    summary_report = QualityValidator.validate_json_summary(updated_summary)
    print_log(f"摘要质量: {summary_report.score}分 ({summary_report.level.value})", level="info")
    
    # 如果摘要质量不佳，保留原摘要的某些字段
    if summary_report.score < 60:
        print_log("摘要质量较低，保留部分原始信息", level="warning")
        for key in ["module", "type", "description"]:
            if key in current_summary and not updated_summary.get(key):
                updated_summary[key] = current_summary[key]
    
    # 6. 存储推理记录
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    decisions = extract_decisions_from_qa(qa_history)
    store_reasoning(
        entity_name=entity_name,
        reasoning_type="local_improved",
        round_goal=phase.value,
        qa_history=qa_history,
        decisions=decisions,
        metadata={
            "phase": phase.value,
            "avg_quality_score": avg_quality,
            "summary_quality": summary_report.score,
            "quality_issues": summary_report.issues[:5]  # 只存储前5个问题
        }
    )
    
    return updated_summary, qa_history, avg_quality

async def run_full_improved_reasoning(
    entity_name: str,
    initial_summary: Dict[str, Any],
    global_constraints: Optional[Dict[str, Any]] = None,
    phases: Optional[List[ReasoningPhase]] = None,
    min_quality_threshold: float = 70.0
) -> Dict[str, Any]:
    """
    运行完整的改进推理流程。
    
    Args:
        entity_name: 实体名称
        initial_summary: 初始摘要
        global_constraints: 全局约束
        phases: 要运行的阶段列表（默认运行所有）
        min_quality_threshold: 最低质量阈值
        
    Returns:
        Dict[str, Any]: 最终的实体摘要
    """
    if phases is None:
        phases = list(ReasoningPhase)
    
    current_summary = initial_summary
    all_qa_history = []
    phases_output = {}
    total_quality_scores = []
    
    for phase in phases:
        # 运行单个阶段
        updated_summary, phase_qa, avg_quality = await run_improved_reasoning_phase(
            entity_name=entity_name,
            phase=phase,
            current_summary=current_summary,
            previous_phases_output=phases_output,
            global_constraints=global_constraints
        )
        
        # 更新状态
        current_summary = updated_summary
        all_qa_history.extend(phase_qa)
        phases_output[phase.value] = {
            "qa_count": len(phase_qa),
            "avg_quality": avg_quality,
            "key_decisions": [qa["answer"][:100] + "..." for qa in phase_qa[:2]]
        }
        total_quality_scores.append(avg_quality)
        
        # 检查质量是否达标
        if avg_quality < min_quality_threshold:
            print_log(
                f"⚠️ {phase.value} 阶段平均质量 ({avg_quality:.1f}) 低于阈值 ({min_quality_threshold})",
                level="warning"
            )
    
    # 计算整体质量
    overall_quality = sum(total_quality_scores) / len(total_quality_scores) if total_quality_scores else 0
    
    print_log(f"🎉 {entity_name} 的改进推理完成！")
    print_log(f"📊 整体质量评分: {overall_quality:.1f}/100")
    print_log(f"📝 共生成 {len(all_qa_history)} 个问答对")
    
    # 添加元数据
    current_summary["_metadata"] = {
        "reasoning_version": "improved_v1",
        "phases_completed": len(phases),
        "overall_quality_score": overall_quality,
        "total_qa_pairs": len(all_qa_history)
    }
    
    return current_summary

# 兼容性包装函数
async def run_local_reasoning_with_quality(
    entity_name: str,
    entity_summary: Dict[str, Any],
    round_goal: str,
    previous_qa: List[Dict[str, str]] = None,
    global_constraints: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    带质量控制的局部推理（兼容旧接口）。
    
    Args:
        entity_name: 实体名称
        entity_summary: 实体摘要
        round_goal: 推理目标
        previous_qa: 之前的问答
        global_constraints: 全局约束
        
    Returns:
        Tuple: (更新的摘要, 问答历史)
    """
    # 映射旧目标到新阶段
    phase_mapping = {
        "上下文理解与基础架构识别": ReasoningPhase.FUNCTION_DEFINITION,
        "架构模式与最佳实践应用": ReasoningPhase.TECHNICAL_IMPLEMENTATION,
        "一致性检查与冲突解决": ReasoningPhase.INTEGRATION_DESIGN,
        "深度架构精细化": ReasoningPhase.QUALITY_ASSURANCE
    }
    
    phase = phase_mapping.get(round_goal, ReasoningPhase.FUNCTION_DEFINITION)
    
    # 运行改进的推理
    updated_summary, qa_history, _ = await run_improved_reasoning_phase(
        entity_name=entity_name,
        phase=phase,
        current_summary=entity_summary,
        previous_phases_output={},
        global_constraints=global_constraints
    )
    
    # 转换为旧格式
    simple_qa = [{"question": qa["question"], "answer": qa["answer"]} for qa in qa_history]
    
    return updated_summary, simple_qa