import os
import json
from clarifier_v2.structured_summarizer import summarize_entity
from clarifier_v2.rag_retriever import embedding_retrieve

# 保存已处理实体的集合，防止重复处理和无限递归
processed_entities = set()

async def recursive_refine(entity, summary, all_docs, schema, output_dir, depth=0):
    """递归细化实体结构
    
    Args:
        entity: 当前处理的实体
        summary: 当前实体的总结
        all_docs: 所有文档内容
        schema: schema格式
        output_dir: 输出目录
        depth: 递归深度
    """
    # 防止无限递归
    if depth > 3:
        print(f"⚠️ 达到最大递归深度 (depth={depth})，停止细化: {entity['name']}")
        return
        
    # 构建实体唯一标识
    entity_key = f"{entity.get('name')}|{entity.get('type')}|{entity.get('parent')}"
    
    # 如果已经处理过，就跳过
    if entity_key in processed_entities:
        print(f"⚠️ 实体已处理过，跳过: {entity['name']}")
        return
    
    # 标记为已处理
    processed_entities.add(entity_key)
    
    # 处理后端部分
    backend = summary.get("backend", {})
    for key in ["dtos", "services", "controllers", "repositories"]:
        items = backend.get(key, {})
        if isinstance(items, dict):
            for sub_name in items.keys():
                # 处理自引用情况：保留自引用但不递归处理
                if sub_name == entity.get('name'):
                    print(f"📌 识别到自引用: {sub_name} (保留但不递归处理)")
                    continue
                    
                sub_entity = {"name": sub_name, "type": key[:-1].capitalize(), "parent": entity["name"]}
                sub_key = f"{sub_name}|{key[:-1].capitalize()}|{entity['name']}"
                
                # 如果已经处理过这个子实体，就跳过
                if sub_key in processed_entities:
                    print(f"⚠️ 子实体已处理过，跳过: {sub_name}")
                    continue
                    
                print(f"📦 处理子实体: {sub_name} (类型: {key[:-1].capitalize()}, 父级: {entity['name']})")
                sub_context = embedding_retrieve(sub_name, all_docs)
                sub_summary = await summarize_entity(sub_entity, sub_context, schema)
                save_summary(sub_entity["name"], sub_summary, output_dir)
                await recursive_refine(sub_entity, sub_summary, all_docs, schema, output_dir, depth + 1)
        elif isinstance(items, list):
            for sub_name in items:
                # 跳过空字符串或None
                if not sub_name:
                    continue
                    
                # 处理自引用情况：保留自引用但不递归处理
                if sub_name == entity.get('name'):
                    print(f"📌 识别到自引用: {sub_name} (保留但不递归处理)")
                    continue
                    
                sub_entity = {"name": sub_name, "type": key[:-1].capitalize(), "parent": entity["name"]}
                sub_key = f"{sub_name}|{key[:-1].capitalize()}|{entity['name']}"
                
                # 如果已经处理过这个子实体，就跳过
                if sub_key in processed_entities:
                    print(f"⚠️ 子实体已处理过，跳过: {sub_name}")
                    continue
                    
                print(f"📦 处理子实体: {sub_name} (类型: {key[:-1].capitalize()}, 父级: {entity['name']})")
                sub_context = embedding_retrieve(sub_name, all_docs)
                sub_summary = await summarize_entity(sub_entity, sub_context, schema)
                save_summary(sub_entity["name"], sub_summary, output_dir)
                await recursive_refine(sub_entity, sub_summary, all_docs, schema, output_dir, depth + 1)

def save_summary(name, summary, output_dir):
    # 处理可能包含路径分隔符的名称
    safe_name = name.replace('/', '_').replace('\\', '_')
    mod_dir = os.path.join(output_dir, safe_name)
    os.makedirs(mod_dir, exist_ok=True)
    with open(os.path.join(mod_dir, "full_summary.json"), "w") as f:
        json.dump(summary, f, indent=2) 