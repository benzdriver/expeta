"""
全局推理链模块。
负责集成系统分析和约束生成，形成完整的全局架构推理链。
提供分析文档、生成架构风格和系统约束的端到端流程。
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from reasoning.global_reasoning.system_analyzer import analyze_system_type, determine_architecture_style
from reasoning.global_reasoning.constraints_generator import generate_constraints, generate_module_guidelines
from knowledge.entity_storage import store_global_decisions, retrieve_global_decisions
from document_processing.content_analyzer import analyze_document_content

# 默认系统名称
DEFAULT_SYSTEM_NAME = "current_system"

# 配置日志
logger = logging.getLogger(__name__)

def extract_system_name_from_docs(documents: str) -> str:
    """
    从文档内容中提取系统名称
    
    Args:
        documents: 文档内容
        
    Returns:
        str: 提取的系统名称，如果未找到则返回默认名称
    """
    # 尝试从标题或开头部分提取系统名称
    patterns = [
        r"# ([^\n]+)",                       # Markdown 标题
        r"<title>([^<]+)</title>",           # HTML 标题
        r"系统名称[：:]\s*([^\n]+)",         # 中文格式
        r"System Name[：:]\s*([^\n]+)",      # 英文格式
        r"^([A-Za-z0-9\s]+)\s*-\s*.+",       # 常见标题格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, documents[:2000])  # 只在前2000个字符中搜索
        if match:
            system_name = match.group(1).strip()
            if system_name:
                return system_name
    
    # 未找到系统名称，返回默认值
    return DEFAULT_SYSTEM_NAME

class GlobalReasoningChain:
    """全局架构推理链，负责整体系统分析和约束生成"""
    
    def __init__(self):
        self.result_cache = {}
        self.system_name = DEFAULT_SYSTEM_NAME
    
    async def run(self, documents: str) -> Dict[str, Any]:
        """
        运行完整的全局推理链
        
        Args:
            documents: 文档内容
            
        Returns:
            Dict[str, Any]: 包含系统分析、架构风格和全局约束的结果
        """
        logger.info("开始全局架构推理...")
        
        # 尝试从文档中提取系统名称
        self.system_name = extract_system_name_from_docs(documents)
        logger.info(f"识别系统名称: {self.system_name}")
        
        # 检查缓存中是否已有结果
        existing_decisions = await retrieve_global_decisions(self.system_name)
        if existing_decisions:
            logger.info("找到现有的全局决策，将基于此继续...")
            return existing_decisions
        
        # 第一步：系统分析
        logger.info("步骤 1/3: 系统类型分析")
        system_analysis = await analyze_system_type(documents)
        self.result_cache["system_analysis"] = system_analysis
        
        # 第二步：架构风格确定
        logger.info("步骤 2/3: 架构风格确定")
        architecture_style = await determine_architecture_style(system_analysis)
        self.result_cache["architecture_style"] = architecture_style
        
        # 第三步：全局约束生成
        logger.info("步骤 3/3: 全局约束生成")
        constraints = await generate_constraints(system_analysis, architecture_style)
        self.result_cache["constraints"] = constraints
        
        # 组合完整结果
        complete_result = {
            "systemAnalysis": system_analysis,
            "architectureStyle": architecture_style,
            "constraints": constraints
        }
        
        # 存储到知识库
        await store_global_decisions(self.system_name, complete_result)
        
        logger.info("全局架构推理完成！")
        return complete_result
    
    async def generate_module_specific_guidelines(self, module_type: str) -> Dict[str, Any]:
        """
        为特定类型的模块生成指导原则
        
        Args:
            module_type: 模块类型 (如 "frontend", "backend", "api", "database")
            
        Returns:
            Dict[str, Any]: 模块特定的指导原则
        """
        # 确保已有全局约束
        if "constraints" not in self.result_cache:
            existing_decisions = await retrieve_global_decisions(self.system_name)
            if existing_decisions and "constraints" in existing_decisions:
                constraints = existing_decisions["constraints"]
            else:
                raise ValueError("必须先运行全局推理链才能生成模块指导原则")
        else:
            constraints = self.result_cache["constraints"]
        
        # 生成模块特定的指导原则
        guidelines = await generate_module_guidelines(constraints, module_type)
        return guidelines
    
    def get_result(self, key: Optional[str] = None) -> Any:
        """
        获取推理结果
        
        Args:
            key: 结果键名，如果为None则返回全部结果
            
        Returns:
            Any: 推理结果
        """
        if key:
            return self.result_cache.get(key)
        return self.result_cache

async def run_global_reasoning(documents: str) -> Dict[str, Any]:
    """
    便捷函数，运行全局推理链
    
    Args:
        documents: 文档内容
        
    Returns:
        Dict[str, Any]: 全局推理结果
    """
    chain = GlobalReasoningChain()
    return await chain.run(documents)

async def get_module_guidelines(module_type: str) -> Dict[str, Any]:
    """
    便捷函数，获取模块指导原则
    
    Args:
        module_type: 模块类型
        
    Returns:
        Dict[str, Any]: 模块指导原则
    """
    chain = GlobalReasoningChain()
    return await chain.generate_module_specific_guidelines(module_type) 