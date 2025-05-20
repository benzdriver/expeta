import re
import json
from pathlib import Path
from llm.llm_executor import run_prompt
from llm.chat_openai import chat
import tiktoken
from llm.token_splitter import get_optimal_chunk_size
import os

from prompt_templates.clarifier.clarifier_prompt_template import get_clarifier_prompt
from clarifier.schema.full_summary_schema import full_summary_schema

tokenizer = tiktoken.encoding_for_model("gpt-4o")

MODEL_NAME = "gpt-4o"

def parse_module_list(text: str):
    print("=== LLM 原始返回内容 ===")
    print(text)
    print("=====================")
    cleaned = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    return json.loads(cleaned)

def load_all_docs(input_dir: Path) -> str:
    all_text = ""
    for file in sorted(input_dir.glob("*.md")):
        all_text += f"\n\n### FILE: {file.name} ###\n\n"
        all_text += file.read_text(encoding="utf-8")
    return all_text

def get_schema_str():
    # 将 full_summary_schema dict 转为格式化字符串
    return json.dumps(full_summary_schema, indent=2)

async def run_embedding_pipeline():
    from clarifier.vector_builder import build_vector_database
    print("[Embedding] data/vector 为空，正在生成文档embedding...")
    await build_vector_database()

async def summarize_all_to_structured_json(input_dir: Path, output_path: Path):
    # 强制输出到 v2/modules 目录
    v2_output_path = Path("data/output/v2/modules")
    v2_output_path.mkdir(parents=True, exist_ok=True)
    output_path = v2_output_path
    # 检查 data/vector 是否为空
    vector_dir = Path("data/vector")
    if not any(vector_dir.iterdir()):
        await run_embedding_pipeline()
    all_text = load_all_docs(input_dir)
    schema_str = get_schema_str()
    print("\U0001f9e0 Sending to LLM for multi-module structured summary...")

    # 动态计算分块大小（临时强制更小分块）
    total_tokens = len(tokenizer.encode(all_text))
    # max_input_tokens = get_optimal_chunk_size(total_tokens, model=MODEL_NAME)
    max_input_tokens = 2000  # 更小分块，便于debug
    print(f"[分块策略] 总tokens: {total_tokens}, max_input_tokens: {max_input_tokens}")

    def strong_prompt(doc_text, schema, chunk_idx, total_chunks):
        base = get_clarifier_prompt(doc_text, schema, chunk_idx, total_chunks)
        return base + "\nStrictly output only a valid JSON array, no explanation, no markdown, no extra text."

    module_summaries = await run_prompt(
        chat=chat,
        user_message=all_text,
        model=MODEL_NAME,
        tokenizer=tokenizer,
        max_input_tokens=max_input_tokens,
        parse_response=parse_module_list,  # 解析为 list[dict]
        get_system_prompt=lambda i, total: strong_prompt(all_text, schema_str, i, total)
    )

    # 聚合、去重
    aggregated = {}
    def merge_module(existing, new):
        # 合并所有字段，支持列表、字典、字符串
        for key in new:
            if key not in existing or not existing[key]:
                existing[key] = new[key]
            elif isinstance(existing[key], list) and isinstance(new[key], list):
                for item in new[key]:
                    if item not in existing[key]:
                        existing[key].append(item)
            elif isinstance(existing[key], dict) and isinstance(new[key], dict):
                for subk, subv in new[key].items():
                    if subk not in existing[key]:
                        existing[key][subk] = subv
            elif isinstance(existing[key], str) and isinstance(new[key], str):
                if existing[key] != new[key]:
                    existing[key] = [existing[key], new[key]]
        # 可选：合并 parent_module 字段
        if "parent_module" in new and ("parent_module" not in existing or not existing["parent_module"]):
            existing["parent_module"] = new["parent_module"]

    for module in module_summaries:
        name = module.get("module", "UnknownModule")
        if name not in aggregated:
            aggregated[name] = module
        else:
            merge_module(aggregated[name], module)
    # 输出
    for name, data in aggregated.items():
        mod_dir = output_path / name
        mod_dir.mkdir(parents=True, exist_ok=True)
        with open(mod_dir / "full_summary.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"\u2705 Module '{name}' summary saved to {mod_dir/'full_summary.json'}")
