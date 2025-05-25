"""
应用层集成测试
测试apps目录下的应用入口脚本
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入被测模块
from apps.run_global_reasoning import run_pipeline as run_global_pipeline
from apps.run_local_reasoning import run_pipeline as run_local_pipeline, process_entity, load_documents
from apps.run_full_pipeline import run_pipeline as run_full_pipeline

@pytest.mark.asyncio
async def test_load_documents(sample_input_files):
    """测试文档加载功能"""
    
    # 执行测试
    all_text = await load_documents(str(sample_input_files))
    
    # 验证结果
    assert all_text
    assert isinstance(all_text, str)
    assert "ThinkForward AI" in all_text
    assert "用户认证与资料管理服务" in all_text
    assert "评估与路径建议服务" in all_text

@pytest.mark.asyncio
async def test_global_reasoning_pipeline(sample_input_files, mock_llm, test_data_dir):
    """测试全局推理流水线"""
    
    # 设置输出目录
    output_dir = test_data_dir / "output" / "global"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 模拟全局推理依赖
    with patch("apps.run_global_reasoning.analyze_system", side_effect=mock_analyze_system), \
         patch("apps.run_global_reasoning.generate_constraints", side_effect=mock_generate_constraints), \
         patch("apps.run_global_reasoning.run_global_reasoning", side_effect=mock_run_global_reasoning), \
         patch("apps.run_global_reasoning.store_entity_summary", return_value=True):
        
        # 执行测试
        results = await run_global_pipeline(str(sample_input_files), str(output_dir))
        
        # 验证结果
        assert results
        assert isinstance(results, dict)
        assert "system_analysis" in results
        assert "constraints" in results
        
        # 验证输出文件
        assert (output_dir / "system_analysis.json").exists()
        assert (output_dir / "architecture_charter.md").exists()
        assert (output_dir / "architecture_charter.json").exists()

@pytest.mark.asyncio
async def test_process_entity(mock_llm, test_data_dir, sample_input_text, sample_global_constraints):
    """测试实体处理功能"""
    
    # 设置输出目录
    output_dir = test_data_dir / "output" / "entity"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 准备测试数据
    entity = {"name": "UserService", "type": "Service", "parent": "Core"}
    global_results = {"constraints": sample_global_constraints}
    
    # 模拟依赖
    with patch("apps.run_local_reasoning.retrieve_context_for_entity", return_value="用户认证与资料管理服务相关的文档内容"), \
         patch("apps.run_local_reasoning.generate_initial_summary", return_value={
             "module": "用户认证与资料管理服务",
             "description": "管理用户身份验证和个人资料",
             "components": [],
             "interfaces": [],
             "dependencies": []
         }), \
         patch("apps.run_local_reasoning.run_local_reasoning", side_effect=mock_run_local_reasoning), \
         patch("apps.run_local_reasoning.store_entity_summary", return_value=True):
        
        # 执行测试
        result = await process_entity(entity, sample_input_text, global_results, str(output_dir), 2)
        
        # 验证结果
        assert result
        assert isinstance(result, dict)
        assert "module" in result
        assert result["module"] == "用户认证与资料管理服务"
        
        # 验证输出文件
        entity_dir = output_dir / "UserService"
        assert entity_dir.exists()
        assert (entity_dir / "full_summary.json").exists()
        assert (entity_dir / "architecture.md").exists()

@pytest.mark.asyncio
async def test_local_reasoning_pipeline(mock_llm, test_data_dir, sample_input_files, sample_entity_data, sample_global_constraints):
    """测试局部推理流水线"""
    
    # 设置输出目录
    output_dir = test_data_dir / "output" / "local"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 准备测试数据
    entity_name = "UserService"
    global_results = {"constraints": sample_global_constraints}
    
    # 模拟依赖
    with patch("apps.run_local_reasoning.load_documents", return_value="用户认证与资料管理服务相关的文档内容"), \
         patch("apps.run_local_reasoning.process_entity", side_effect=mock_process_entity):
        
        # 执行测试
        await run_local_pipeline(entity_name, str(sample_input_files), str(output_dir), 2)
        
        # 验证输出文件
        entity_dir = output_dir / "UserService"
        assert entity_dir.exists()
        assert (entity_dir / "full_summary.json").exists()

@pytest.mark.asyncio
async def test_full_pipeline(mock_llm, test_data_dir, sample_input_files):
    """测试完整流水线"""
    
    # 设置输出目录
    output_dir = test_data_dir / "output" / "full"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 模拟依赖
    with patch("apps.run_full_pipeline.load_documents", return_value="完整文档内容"), \
         patch("apps.run_full_pipeline.run_global_reasoning", return_value={
             "system_analysis": {"system_type": "加拿大移民申请SaaS平台"},
             "constraints": {"命名规范": {"类命名": "驼峰命名法"}},
             "architecture_charter": {"架构风格": "Serverless架构"}
         }), \
         patch("apps.run_full_pipeline.discover_entities", return_value=[
             {"name": "UserService", "type": "Service", "parent": "Core"},
             {"name": "AssessmentService", "type": "Service", "parent": "Core"}
         ]), \
         patch("apps.run_full_pipeline.process_entity", side_effect=mock_process_entity), \
         patch("apps.run_full_pipeline.generate_architecture_diagram", return_value=None), \
         patch("apps.run_full_pipeline.generate_index_page", return_value=None):
        
        # 执行测试
        await run_full_pipeline(str(sample_input_files), str(output_dir), 2)
        
        # 验证输出文件
        assert (output_dir / "system_analysis.json").exists()
        assert (output_dir / "architecture_charter.md").exists()
        assert (output_dir / "UserService").exists()
        assert (output_dir / "AssessmentService").exists()

# 模拟函数

async def mock_analyze_system(*args, **kwargs):
    """模拟系统分析"""
    return {
        "system_type": "加拿大移民申请SaaS平台",
        "architecture_style": "Serverless架构",
        "technology_stack": {
            "frontend": "Next.js + React + Tailwind CSS",
            "backend": "Serverless函数 (Node.js)",
            "database": ["MongoDB Atlas"],
            "storage": "AWS S3 / Azure Blob Storage",
            "authentication": "AWS Cognito / Auth0",
            "ai": "OpenAI API"
        }
    }

async def mock_generate_constraints(*args, **kwargs):
    """模拟约束生成"""
    return {
        "命名规范": {"类命名": "驼峰命名法"},
        "API设计": {"REST规范": "遵循RESTful设计原则"},
        "安全规范": {"认证": "JWT认证", "数据保护": "所有敏感数据加密存储"}
    }

async def mock_run_global_reasoning(*args, **kwargs):
    """模拟全局推理"""
    return {
        "system_analysis": {
            "system_type": "加拿大移民申请SaaS平台",
            "architecture_style": "Serverless架构"
        },
        "constraints": {
            "命名规范": {"类命名": "驼峰命名法"},
            "API设计": {"REST规范": "遵循RESTful设计原则"}
        },
        "architecture_charter": {
            "架构风格": "Serverless架构",
            "技术栈": {"前端": "Next.js + React", "后端": "Serverless函数 (Node.js)"}
        }
    }

async def mock_run_local_reasoning(*args, **kwargs):
    """模拟局部推理"""
    entity_name = args[0] if args else kwargs.get("entity_name", "")
    
    if "UserService" in entity_name:
        return {
            "module": "用户认证与资料管理服务",
            "description": "负责用户注册、登录、个人资料管理和认证授权",
            "components": ["AuthController", "ProfileService", "UserRepository"],
            "interfaces": ["REST API", "Cognito/Auth0集成"],
            "dependencies": ["评估服务", "通知服务"],
            "frontend": {
                "pages": ["登录页", "注册页", "用户档案页"],
                "components": ["登录表单", "注册表单", "个人资料表单"]
            },
            "backend": {
                "controllers": ["AuthController", "ProfileController"],
                "services": ["AuthService", "ProfileService"]
            }
        }
    elif "AssessmentService" in entity_name:
        return {
            "module": "评估与路径建议服务",
            "description": "管理移民申请者的资格评估流程与路径建议",
            "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
            "interfaces": ["REST API", "OpenAI集成"],
            "dependencies": ["用户服务", "表格服务"],
            "frontend": {
                "pages": ["评估问卷页", "评估结果页", "路径比较页"]
            },
            "backend": {
                "controllers": ["AssessmentController", "PathwayController"],
                "services": ["EligibilityService", "RecommendationService"]
            }
        }
    else:
        return {
            "module": f"{entity_name}",
            "description": f"{entity_name}的默认描述",
            "components": ["Controller", "Service", "Repository"],
            "interfaces": ["REST API"],
            "dependencies": []
        }

async def mock_process_entity(*args, **kwargs):
    """模拟实体处理"""
    entity = args[0] if args else kwargs.get("entity", {})
    entity_name = entity.get("name", "Unknown")
    
    # 创建输出目录
    output_dir = args[3] if len(args) > 3 else kwargs.get("output_dir", "")
    if output_dir:
        entity_dir = Path(output_dir) / entity_name
        entity_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建JSON摘要
        summary = await mock_run_local_reasoning(entity_name=entity_name)
        with open(entity_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 创建MD文档
        with open(entity_dir / "architecture.md", "w", encoding="utf-8") as f:
            f.write(f"# {entity_name} 架构设计\n\n")
            f.write(f"## 描述\n\n{summary['description']}\n\n")
            f.write("## 组件\n\n")
            for component in summary["components"]:
                f.write(f"- {component}\n")
    
    return await mock_run_local_reasoning(entity_name=entity_name) 