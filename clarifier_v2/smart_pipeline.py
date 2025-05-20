print("=== pipeline 启动 ===")
from dotenv import load_dotenv
load_dotenv()
import asyncio
from pathlib import Path
from clarifier_v2.entity_discovery import discover_entities
from clarifier_v2.rag_retriever import (
    embedding_retrieve, 
    store_entity_summary, 
    retrieve_entity_summaries,
    retrieve_dependencies
)
from clarifier_v2.structured_summarizer import summarize_entity
from clarifier_v2.postprocess import recursive_refine, save_summary, processed_entities
from clarifier.schema.full_summary_schema import full_summary_schema
import json
import os

async def process_entity(entity, all_text, schema, output_path, processed=None, depth=0):
    """处理单个实体并验证依赖关系
    
    Args:
        entity: 实体信息
        all_text: 所有文档内容
        schema: schema格式
        output_path: 输出目录
        processed: 已处理的实体集合
        depth: 递归深度
    """
    if processed is None:
        processed = set()
    
    # 构建实体唯一标识
    entity_key = f"{entity.get('name')}|{entity.get('type')}|{entity.get('parent')}"
    
    # 如果已经处理过，就跳过
    if entity_key in processed:
        print(f"⚠️ 实体已处理过，跳过: {entity['name']}")
        return
    
    # 标记为已处理
    processed.add(entity_key)
    
    # 获取相关上下文
    print(f"🔍 获取实体 {entity['name']} 的上下文...")
    context = embedding_retrieve(entity["name"], all_text)
    
    # 生成总结
    print(f"📝 生成结构化总结...")
    summary = await summarize_entity(entity, context, schema)
    
    # 验证依赖关系
    if "dependencies" in summary and summary["dependencies"]:
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
    
    # 保存总结
    save_summary(entity["name"], summary, output_path)
    
    # 存储到向量数据库
    print(f"📥 存储摘要到向量数据库...")
    doc = store_entity_summary(entity["name"], summary)
    if doc:
        print(f"✅ 摘要已存储到向量数据库")
    else:
        print(f"❌ 存储到向量数据库失败")
    
    # 递归细化
    print(f"细化实体: {entity['name']}")
    await recursive_refine(entity, summary, all_text, schema, output_path, depth=0)

async def run_smart_pipeline(input_dir: str, output_dir: str):
    """运行智能 pipeline 进行文档分析和总结
    
    Args:
        input_dir: 输入文档目录
        output_dir: 输出目录
    """
    # 清空已处理实体集合，防止多次运行时出现问题
    processed_entities.clear()
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("📚 读取文档...")
    all_text = ""
    for file in sorted(input_path.glob("*.md")):
        all_text += f"\n\n### FILE: {file.name} ###\n\n"
        all_text += file.read_text(encoding="utf-8")
    schema = json.dumps(full_summary_schema, indent=2)

    print("🔍 发现实体...")
    entities = await discover_entities(all_text)
    print(f"发现实体: {[e['name'] for e in entities]}")

    print("📝 生成结构化总结...")
    
    # 按复杂度排序实体，优先处理基础实体
    # 1. 首先处理没有"/"的简单实体
    # 2. 然后处理包含"/"的复杂实体，按照路径深度排序
    simple_entities = [e for e in entities if '/' not in e.get('name', '')]
    complex_entities = [e for e in entities if '/' in e.get('name', '')]
    
    # 按名称长度/复杂度排序
    simple_entities.sort(key=lambda e: len(e.get('name', '')))
    complex_entities.sort(key=lambda e: len(e.get('name', '').split('/')))
    
    # 合并排序后的列表
    sorted_entities = simple_entities + complex_entities
    
    print(f"🔢 处理顺序:")
    for i, entity in enumerate(sorted_entities):
        print(f"  {i+1}. {entity.get('name')}")
    
    # 逐个处理实体
    for entity in sorted_entities:
        # 跳过已处理的实体
        entity_key = f"{entity.get('name')}|{entity.get('type')}|{entity.get('parent')}"
        if entity_key in processed_entities:
            print(f"⚠️ 实体已处理过，跳过: {entity['name']}")
            continue
            
        print(f"\n处理实体: {entity['name']}")
        await process_entity(entity, all_text, schema, output_path, processed_entities)

    print("\n✅ Pipeline 完成!")
    print(f"输出目录: {output_path}")
    print(f"处理的实体总数: {len(processed_entities)}")

def main():
    """主函数"""
    import sys
    
    # 设置默认路径
    input_dir = "data/input"
    output_dir = "data/output/v2/smart_modules"
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # 运行 pipeline
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    asyncio.run(run_smart_pipeline(input_dir, output_dir))

if __name__ == "__main__":
    main() 