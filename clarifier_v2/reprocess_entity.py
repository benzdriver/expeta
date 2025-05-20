#!/usr/bin/env python3
"""
重新处理特定实体的脚本
用法：python -m clarifier_v2.reprocess_entity auth_login data/output/v2/smart_modules_improved
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from clarifier_v2.structured_summarizer import summarize_entity
from clarifier_v2.rag_retriever import (
    embedding_retrieve, 
    store_entity_summary, 
    retrieve_entity_summaries,
    retrieve_dependencies
)
from clarifier.schema.full_summary_schema import full_summary_schema

async def reprocess_entity(entity_name, output_dir, validate_dependencies=True, store_to_vector_db=True):
    """重新处理特定实体
    
    Args:
        entity_name: 实体名称
        output_dir: 输出目录
        validate_dependencies: 是否验证依赖关系
        store_to_vector_db: 是否存储到向量数据库
    """
    # 读取文档内容
    print(f"📚 读取文档...")
    all_text = ""
    input_path = Path("data/input")
    for file in sorted(input_path.glob("*.md")):
        all_text += f"\n\n### FILE: {file.name} ###\n\n"
        all_text += file.read_text(encoding="utf-8")
    
    # 准备schema
    schema = json.dumps(full_summary_schema, indent=2)
    
    # 构建实体信息
    entity = {"name": entity_name, "type": "Unknown"}
    
    # 获取已有的摘要信息（如果有）
    existing_summaries = retrieve_entity_summaries(entity_name, top_k=1)
    if existing_summaries:
        print(f"📋 找到已有的摘要信息: {entity_name}")
        entity_type = existing_summaries[0].get("module", "Unknown")
        if entity_type and entity_type != "unknown":
            entity["type"] = entity_type
    
    # 获取相关上下文
    print(f"🔍 获取实体 {entity_name} 的上下文...")
    context = embedding_retrieve(entity_name, all_text)
    
    # 生成总结
    print(f"📝 生成结构化总结...")
    summary = await summarize_entity(entity, context, schema)
    
    # 验证依赖关系
    if validate_dependencies and "dependencies" in summary and summary["dependencies"]:
        print(f"🔄 验证依赖关系...")
        dependencies = summary["dependencies"]
        valid_deps = []
        invalid_deps = []
        
        # 获取依赖项的摘要
        dep_summaries = retrieve_dependencies(dependencies)
        
        for dep in dependencies:
            if dep in dep_summaries:
                print(f"✅ 依赖项有效: {dep}")
                valid_deps.append(dep)
            else:
                print(f"⚠️ 依赖项可能无效: {dep} (未找到相关摘要)")
                # 也可以尝试在原始文档中查找
                dep_context = embedding_retrieve(dep, all_text)
                if dep and len(dep_context.strip()) > 100:  # 简单检查是否有足够上下文
                    print(f"📄 在原始文档中找到依赖项信息: {dep}")
                    valid_deps.append(dep)
                else:
                    print(f"❌ 无法验证依赖项: {dep}")
                    invalid_deps.append(dep)
        
        # 更新依赖列表，只保留有效的依赖
        if invalid_deps:
            print(f"🧹 从依赖列表中移除无效依赖: {invalid_deps}")
            summary["dependencies"] = valid_deps
            # 也可以选择保留无效依赖，但标记为未验证
            # summary["unverified_dependencies"] = invalid_deps
    
    # 保存总结
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 处理可能包含路径分隔符的名称
    safe_name = entity_name.replace('/', '_').replace('\\', '_')
    mod_dir = os.path.join(output_path, safe_name)
    os.makedirs(mod_dir, exist_ok=True)
    
    summary_file = os.path.join(mod_dir, "full_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ 已保存到 {summary_file}")
    
    # 存储到向量数据库
    if store_to_vector_db:
        print(f"📥 存储摘要到向量数据库...")
        doc = store_entity_summary(entity_name, summary)
        if doc:
            print(f"✅ 摘要已存储到向量数据库")
        else:
            print(f"❌ 存储到向量数据库失败")
    
    return summary

async def batch_process_entities(entity_list, output_dir):
    """批量处理多个实体
    
    Args:
        entity_list: 实体名称列表
        output_dir: 输出目录
    """
    # 按照依赖的复杂度排序，先处理基础实体
    entities_to_process = sorted(entity_list, key=lambda x: len(x.split('/')))
    
    print(f"🔍 批量处理 {len(entities_to_process)} 个实体...")
    
    for entity_name in entities_to_process:
        print(f"\n🔄 处理实体: {entity_name}")
        await reprocess_entity(entity_name, output_dir)
    
    print(f"\n✅ 批量处理完成")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python -m clarifier_v2.reprocess_entity [entity_name] [output_dir]")
        print("      python -m clarifier_v2.reprocess_entity --batch [entities_file] [output_dir]")
        print("示例: python -m clarifier_v2.reprocess_entity auth_login data/output/v2/smart_modules_improved")
        print("      python -m clarifier_v2.reprocess_entity --batch entities.txt data/output/v2/smart_modules_improved")
        sys.exit(1)
    
    # 批量处理模式
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("错误: 缺少实体列表文件")
            sys.exit(1)
            
        entities_file = sys.argv[2]
        output_dir = "data/output/v2/smart_modules_improved"
        if len(sys.argv) > 3:
            output_dir = sys.argv[3]
            
        try:
            with open(entities_file, 'r') as f:
                entities = [line.strip() for line in f if line.strip()]
                
            if not entities:
                print("错误: 实体列表为空")
                sys.exit(1)
                
            print(f"📋 从 {entities_file} 读取了 {len(entities)} 个实体")
            print(f"📂 输出目录: {output_dir}")
            
            asyncio.run(batch_process_entities(entities, output_dir))
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            sys.exit(1)
    # 单个实体处理模式
    else:
        entity_name = sys.argv[1]
        output_dir = "data/output/v2/smart_modules_improved"
        if len(sys.argv) > 2:
            output_dir = sys.argv[2]
        
        print(f"🔄 重新处理实体: {entity_name}")
        print(f"📂 输出目录: {output_dir}")
        
        asyncio.run(reprocess_entity(entity_name, output_dir))

if __name__ == "__main__":
    main() 