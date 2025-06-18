"""
Clarifier 系统实施计划 - 基于现有代码的改造
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

# 1. 复用现有的推理引擎，但调整输出
class ClarifierMode(Enum):
    """Clarifier 工作模式"""
    INTERACTIVE = "interactive"  # 交互式澄清
    PRD_ANALYSIS = "prd_analysis"  # PRD 分析

class UnifiedClarifier:
    """统一的 Clarifier 系统"""
    
    def __init__(self, mode: ClarifierMode):
        self.mode = mode
        self.session_data = {
            "mode": mode.value,
            "progress": {},
            "intermediate_results": [],
            "final_summary": None
        }
    
    async def process(self, input_data: Union[str, Dict]) -> Dict[str, Any]:
        """统一的处理入口"""
        if self.mode == ClarifierMode.INTERACTIVE:
            return await self._process_interactive(input_data)
        else:
            return await self._process_prd(input_data)
    
    async def _process_interactive(self, user_input: str) -> Dict[str, Any]:
        """处理交互式澄清"""
        # 复用现有的问答生成器，但调整为业务语言
        from reasoning.local_reasoning.question_generators import generate_questions_for_round
        from reasoning.local_reasoning.answer_generators_improved import generate_specific_answer
        
        # 将技术问题转换为业务问题
        business_questions = await self._generate_business_questions(user_input)
        
        return {
            "type": "interactive",
            "questions": business_questions,
            "current_state": self.session_data
        }
    
    async def _process_prd(self, prd_content: str) -> Dict[str, Any]:
        """处理 PRD 分析 - 复用现有的多轮推理"""
        # 复用现有的文档处理和推理链
        from document_processing.entity_discovery import discover_entities_from_content
        from reasoning.local_reasoning.local_chain_improved import run_full_improved_reasoning
        
        # 但是调整实体发现逻辑，识别业务需求而非技术模块
        business_entities = await self._discover_business_requirements(prd_content)
        
        # 对每个业务需求进行推理
        results = {}
        for entity in business_entities:
            # 使用改造后的推理链
            summary = await self._run_business_reasoning(entity)
            results[entity['name']] = summary
        
        return {
            "type": "prd_analysis",
            "discovered_requirements": business_entities,
            "analysis_results": results,
            "structured_summary": self._merge_to_unified_json(results)
        }
    
    async def _generate_business_questions(self, context: str) -> List[str]:
        """生成业务导向的问题"""
        # 改造提示词，从技术问题转向业务问题
        business_prompt = """
        你是一个产品经理助手，需要帮助用户澄清产品需求。
        
        基于用户的描述，生成3-5个澄清问题：
        1. 问题要用简单的业务语言，避免技术术语
        2. 关注用户价值和业务目标
        3. 问题要具体且易于回答
        
        好的问题示例：
        - "您的目标用户每天会使用这个功能几次？"
        - "这个功能解决了用户的什么具体问题？"
        - "如果没有这个系统，用户现在是怎么完成这个任务的？"
        
        用户描述：{context}
        """
        
        # 使用现有的 LLM 执行器
        from llm_services.executor import run_prompt
        response = await run_prompt(
            system_message="你是一个友好的产品经理助手",
            user_message=business_prompt.format(context=context)
        )
        
        return self._parse_questions(response)
    
    async def _discover_business_requirements(self, prd_content: str) -> List[Dict]:
        """从 PRD 中发现业务需求（而非技术模块）"""
        # 改造实体发现的提示词
        discovery_prompt = """
        分析以下 PRD 文档，识别主要的业务需求和功能模块。
        
        注意：
        1. 识别业务功能而非技术组件
        2. 关注用户故事和使用场景
        3. 提取功能需求而非实现细节
        
        输出格式：
        - 功能名称（如"用户注册流程"而非"UserService"）
        - 功能描述
        - 相关的用户角色
        
        PRD内容：
        {content}
        """
        
        # 复用现有的实体发现逻辑，但改变识别目标
        from llm_services.executor import run_prompt
        response = await run_prompt(
            system_message="你是一个需求分析专家",
            user_message=discovery_prompt.format(content=prd_content)
        )
        
        return self._parse_business_entities(response)
    
    async def _run_business_reasoning(self, entity: Dict) -> Dict[str, Any]:
        """对业务需求进行推理（改造自技术推理）"""
        # 定义业务导向的推理阶段
        BUSINESS_REASONING_PHASES = [
            {
                "phase": "需求理解",
                "focus": ["用户价值", "业务目标", "使用场景"],
                "questions": [
                    "这个功能为用户创造什么价值？",
                    "典型的使用场景是什么？",
                    "成功的标准是什么？"
                ]
            },
            {
                "phase": "功能设计",
                "focus": ["核心功能", "用户流程", "界面要素"],
                "questions": [
                    "用户完成任务的步骤是什么？",
                    "需要哪些信息输入？",
                    "期望的输出结果是什么？"
                ]
            },
            {
                "phase": "约束分析",
                "focus": ["业务规则", "合规要求", "性能期望"],
                "questions": [
                    "有哪些业务规则限制？",
                    "需要遵守哪些法规？",
                    "用户的性能期望是什么？"
                ]
            }
        ]
        
        # 复用改进的推理链，但使用业务阶段
        from knowledge.context_retrieval_improved import FocusedContextBuilder
        
        results = {}
        for phase_config in BUSINESS_REASONING_PHASES:
            # 构建业务上下文
            context = await self._build_business_context(entity, phase_config)
            
            # 生成和回答业务问题
            qa_pairs = await self._generate_business_qa(entity, phase_config, context)
            
            # 更新结果
            results[phase_config["phase"]] = qa_pairs
        
        return self._structure_business_summary(entity, results)
    
    def _merge_to_unified_json(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """将分析结果合并为统一的 JSON 格式"""
        unified = {
            "project": {},
            "business_context": {},
            "users": {},
            "functional_requirements": {
                "core_features": [],
                "user_flows": []
            },
            "non_functional_requirements": {},
            "constraints": {},
            "metadata": {
                "clarification_method": self.mode.value,
                "confidence_scores": {}
            }
        }
        
        # 从各个分析结果中提取和整合信息
        for req_name, analysis in results.items():
            # 提取并填充到统一结构中
            self._extract_to_unified(analysis, unified)
        
        return unified
    
    async def generate_prd_from_summary(self, json_summary: Dict[str, Any]) -> str:
        """从 JSON Summary 生成 PRD 文档"""
        # 使用模板生成 Markdown PRD
        prd_template = self._get_prd_template()
        
        # 填充模板
        prd_content = self._fill_prd_template(prd_template, json_summary)
        
        # 使用 LLM 润色和补充
        enhanced_prd = await self._enhance_prd_with_llm(prd_content, json_summary)
        
        return enhanced_prd
    
    def _get_prd_template(self) -> str:
        """获取 PRD 模板"""
        return """
# {project_name} - 产品需求文档

## 1. 项目概述
- **项目名称**: {project_name}
- **项目类型**: {project_type}
- **版本**: {version}
- **日期**: {date}

## 2. 背景与目标

### 2.1 业务背景
{problem_statement}

### 2.2 项目目标
{goals}

### 2.3 成功指标
{success_metrics}

## 3. 用户与干系人

### 3.1 目标用户
{target_users}

### 3.2 用户需求
{user_needs}

### 3.3 用户故事
{user_stories}

## 4. 功能需求

### 4.1 功能列表
{feature_list}

### 4.2 功能详述
{feature_details}

### 4.3 用户流程
{user_flows}

## 5. 非功能需求

### 5.1 性能要求
{performance}

### 5.2 安全要求
{security}

### 5.3 可用性要求
{usability}

## 6. 约束与依赖

### 6.1 技术约束
{technical_constraints}

### 6.2 业务约束
{business_constraints}

### 6.3 外部依赖
{dependencies}

## 7. 风险与对策
{risks}

## 8. 实施计划
{implementation_plan}

## 附录
- 术语表
- 参考资料
- 修订记录
"""

# 集成现有系统的适配器
class ExistingSystemAdapter:
    """将现有系统功能适配到 Clarifier"""
    
    @staticmethod
    async def adapt_entity_discovery(content: str, target: str = "business") -> List[Dict]:
        """适配实体发现功能"""
        from document_processing.entity_discovery import discover_entities_from_content
        
        if target == "business":
            # 修改提示词，识别业务实体而非技术实体
            # 这里可以通过修改 prompts.py 或传入自定义提示词
            pass
        
        entities = await discover_entities_from_content(content)
        
        # 转换实体格式
        return [ExistingSystemAdapter._convert_to_business_entity(e) for e in entities]
    
    @staticmethod
    async def adapt_reasoning_chain(entity: Dict, reasoning_type: str = "business") -> Dict:
        """适配推理链"""
        from reasoning.local_reasoning.local_chain_improved import run_full_improved_reasoning
        
        if reasoning_type == "business":
            # 使用业务导向的推理配置
            # 可以通过自定义 PhaseConfig 实现
            pass
        
        result = await run_full_improved_reasoning(
            entity_name=entity['name'],
            initial_summary=entity,
            phases=None  # 使用自定义的业务阶段
        )
        
        return result
    
    @staticmethod
    def _convert_to_business_entity(tech_entity: Dict) -> Dict:
        """将技术实体转换为业务实体"""
        return {
            "name": tech_entity.get("module", "").replace("Service", "功能"),
            "type": "business_feature",
            "description": tech_entity.get("description", ""),
            "business_value": "待分析",
            "user_impact": "待分析"
        }

# 使用示例
async def clarify_with_existing_prd():
    """使用现有 PRD 进行澄清"""
    clarifier = UnifiedClarifier(ClarifierMode.PRD_ANALYSIS)
    
    # 读取 PRD
    with open("sample_prd.md", "r") as f:
        prd_content = f.read()
    
    # 分析 PRD
    result = await clarifier.process(prd_content)
    
    # 生成结构化输出
    json_summary = result["structured_summary"]
    
    # 生成增强的 PRD
    enhanced_prd = await clarifier.generate_prd_from_summary(json_summary)
    
    return {
        "json_summary": json_summary,
        "enhanced_prd": enhanced_prd,
        "analysis_details": result["analysis_results"]
    }

async def clarify_interactively():
    """交互式澄清"""
    clarifier = UnifiedClarifier(ClarifierMode.INTERACTIVE)
    
    # 模拟多轮对话
    conversation = []
    
    # 第一轮
    user_input = "我想做一个帮助律师管理案件的系统"
    response = await clarifier.process(user_input)
    
    # 继续对话...
    # 最终生成 JSON Summary 和 PRD
    
    return clarifier.session_data["final_summary"]