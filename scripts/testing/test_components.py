#!/usr/bin/env python3
"""
测试脚本 - 分段测试架构推理系统的各个组件
用法示例:
    # 测试文档内容分析
    python scripts/test_components.py --mode content_analyzer --input data/sample_doc.txt
    
    # 测试初始摘要生成
    python scripts/test_components.py --mode initial_summarizer --input data/sample_doc.txt --entity "ModuleName"
    
    # 测试知识存储
    python scripts/test_components.py --mode knowledge_store --entity "ModuleName" --action save
    
    # 测试本地推理
    python scripts/test_components.py --mode local_reasoning --entity "ModuleName" --rounds 1
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from document_processing.content_analyzer import analyze_document_content
from document_processing.initial_summarizer import generate_initial_summary
from knowledge.entity_storage import retrieve_entity, update_entity, list_entities
from reasoning.local_reasoning.local_chain import run_full_local_reasoning
from reasoning.local_reasoning.question_generators import generate_questions
from reasoning.local_reasoning.answer_generators import generate_answers
from reasoning.local_reasoning.summary_updaters import update_entity_summary
from reasoning.local_reasoning.context_builder import build_context

async def test_content_analyzer(input_file: str, output_file: Optional[str] = None) -> None:
    """测试文档内容分析组件"""
    print(f"📊 测试文档内容分析: {input_file}")
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        document_text = f.read()
    
    # 运行内容分析
    result = await analyze_document_content(document_text)
    
    # 输出结果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ 已保存分析结果到: {output_file}")
    else:
        print("分析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

async def test_initial_summarizer(input_file: str, entity_name: str, output_file: Optional[str] = None) -> None:
    """测试初始摘要生成组件"""
    print(f"📝 测试初始摘要生成: {input_file} -> {entity_name}")
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        document_text = f.read()
    
    # 准备实体信息
    entity = {
        "name": entity_name,
        "type": "module"
    }
    
    # 生成初始摘要
    result = await generate_initial_summary(entity, document_text)
    
    # 输出结果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ 已保存初始摘要到: {output_file}")
    else:
        print("初始摘要:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

async def test_knowledge_store(entity_name: str, action: str, input_file: Optional[str] = None) -> None:
    """测试知识存储组件"""
    print(f"🗃️ 测试知识存储: {action} -> {entity_name}")
    
    if action == "save" and input_file:
        # 从文件加载实体数据
        with open(input_file, 'r', encoding='utf-8') as f:
            entity_data = json.load(f)
        
        # 保存到存储
        success = update_entity(entity_name, entity_data)
        print(f"{'✅ 保存成功' if success else '❌ 保存失败'}")
        
    elif action == "retrieve":
        # 从存储检索实体
        entity_data = retrieve_entity(entity_name)
        if entity_data:
            print("检索结果:")
            print(json.dumps(entity_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 未找到实体: {entity_name}")
    
    elif action == "list":
        # 列出所有实体
        entities = list_entities()
        print(f"存储中的实体 ({len(entities)}):")
        for entity in entities:
            print(f" - {entity}")

async def test_local_reasoning(entity_name: str, rounds: int = 1, constraints_file: Optional[str] = None, input_file: Optional[str] = None) -> None:
    """测试本地推理组件"""
    print(f"🧠 测试本地推理: {entity_name} (轮次: {rounds})")
    
    # 获取实体数据，优先从文件读取
    entity_data = None
    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                entity_data = json.load(f)
            print(f"✅ 从文件加载实体数据: {input_file}")
        except Exception as e:
            print(f"❌ 加载实体数据失败: {e}")
            return
    else:
        # 从存储检索实体数据
        entity_data = retrieve_entity(entity_name)
        if not entity_data:
            print(f"❌ 未找到实体: {entity_name}")
            return
    
    # 加载约束(如果有)
    global_constraints = None
    if constraints_file:
        try:
            with open(constraints_file, 'r', encoding='utf-8') as f:
                global_constraints = json.load(f)
        except Exception as e:
            print(f"❌ 加载约束文件失败: {e}")
            return
    
    if rounds <= 0:
        # 只测试上下文构建
        print("🔍 测试上下文构建...")
        context = await build_context(entity_name, entity_data)
        print(f"生成的上下文长度: {len(context)} 字符")
        
    elif rounds == 1:
        # 测试单轮推理
        print("❓ 测试问题生成...")
        questions = await generate_questions(entity_name, entity_data)
        print(f"生成了 {len(questions)} 个问题:")
        for i, q in enumerate(questions):
            print(f"  {i+1}. {q}")
        
        print("\n💡 测试答案生成...")
        context = await build_context(entity_name, entity_data)
        answers = await generate_answers(questions, context)
        print(f"生成了 {len(answers)} 个答案:")
        for i, (q, a) in enumerate(zip(questions, answers)):
            print(f"  问题 {i+1}: {q}")
            print(f"  答案: {a[:100]}..." if len(a) > 100 else f"  答案: {a}")
            print()
        
        print("\n📝 测试摘要更新...")
        # 为答案生成构建QA对
        qa_pairs = []
        for q, a in zip(questions, answers):
            qa_pairs.append({"question": q, "answer": a})
            
        # 调用更新函数，提供所有必需参数
        updated_summary = await update_entity_summary(
            entity_name=entity_name,
            current_summary=entity_data,
            qa_history=qa_pairs,
            context=context,
            round_goal="深度架构精细化"
        )
        print("更新后的摘要:")
        print(json.dumps(updated_summary, indent=2, ensure_ascii=False)[:500] + "...")
        
    else:
        # 测试完整多轮推理
        print(f"🔄 测试完整推理流程 ({rounds} 轮)...")
        updated_summary = await run_full_local_reasoning(
            entity_name=entity_name,
            initial_summary=entity_data,
            global_constraints=global_constraints,
            max_rounds=rounds
        )
        
        print("最终摘要:")
        print(json.dumps(updated_summary, indent=2, ensure_ascii=False)[:500] + "...")
        
        # 询问是否保存更新后的摘要
        save_result = input("是否保存更新后的摘要? (y/n): ").lower()
        if save_result == 'y':
            success = update_entity(entity_name, updated_summary)
            print(f"{'✅ 保存成功' if success else '❌ 保存失败'}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分段测试架构推理系统组件")
    parser.add_argument("--mode", "-m", required=True, choices=[
        "content_analyzer", 
        "initial_summarizer", 
        "knowledge_store", 
        "local_reasoning"
    ], help="测试模式")
    parser.add_argument("--input", "-i", help="输入文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--entity", "-e", help="实体名称")
    parser.add_argument("--action", "-a", choices=["save", "retrieve", "list"], 
                      default="retrieve", help="知识存储操作")
    parser.add_argument("--rounds", "-r", type=int, default=1, help="推理轮次")
    parser.add_argument("--constraints", "-c", help="约束文件路径")
    
    args = parser.parse_args()
    
    # 根据模式运行不同的测试
    if args.mode == "content_analyzer":
        if not args.input:
            print("❌ 内容分析模式需要提供输入文件 (--input)")
            return
        asyncio.run(test_content_analyzer(args.input, args.output))
        
    elif args.mode == "initial_summarizer":
        if not args.input or not args.entity:
            print("❌ 初始摘要模式需要提供输入文件 (--input) 和实体名称 (--entity)")
            return
        asyncio.run(test_initial_summarizer(args.input, args.entity, args.output))
        
    elif args.mode == "knowledge_store":
        if not args.entity and args.action != "list":
            print("❌ 知识存储模式需要提供实体名称 (--entity)")
            return
        if args.action == "save" and not args.input:
            print("❌ 保存操作需要提供输入文件 (--input)")
            return
        asyncio.run(test_knowledge_store(args.entity, args.action, args.input))
        
    elif args.mode == "local_reasoning":
        if not args.entity:
            print("❌ 本地推理模式需要提供实体名称 (--entity)")
            return
        asyncio.run(test_local_reasoning(args.entity, args.rounds, args.constraints, args.input))

if __name__ == "__main__":
    main() 