import re
import json
from pathlib import Path
from typing import List, Dict
from llm.llm_executor import run_prompt
from llm.chat_openai import chat
import tiktoken
from llm.token_splitter import get_optimal_chunk_size

from prompt_templates.clarifier.clarifier_prompt_template import get_clarifier_prompt
from clarifier.schema.full_summary_schema import full_summary_schema
from clarifier.rag_retriever import embedding_retrieve

tokenizer = tiktoken.encoding_for_model("gpt-4o")
MODEL_NAME = "gpt-4o"

def parse_module_list(text: str) -> List[Dict]:
    """Parse LLM response into a list of module summaries"""
    print("=== LLM Response ===")
    print(text)
    print("==================")
    cleaned = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    return json.loads(cleaned)

def load_all_docs(input_dir: Path) -> str:
    """Load and concatenate all markdown documents"""
    all_text = ""
    for file in sorted(input_dir.glob("*.md")):
        all_text += f"\n\n### FILE: {file.name} ###\n\n"
        all_text += file.read_text(encoding="utf-8")
    return all_text

def merge_module_summaries(existing: Dict, new: Dict) -> Dict:
    """Merge two module summaries, combining lists and preserving unique items"""
    for key, new_value in new.items():
        if key not in existing or not existing[key]:
            existing[key] = new_value
        elif isinstance(existing[key], list) and isinstance(new_value, list):
            # Merge lists, preserving unique items
            existing[key].extend(item for item in new_value if item not in existing[key])
        elif isinstance(existing[key], dict) and isinstance(new_value, dict):
            # Recursively merge dictionaries
            for subk, subv in new_value.items():
                if subk not in existing[key]:
                    existing[key][subk] = subv
                else:
                    existing[key][subk] = merge_module_summaries(existing[key][subk], subv)
    return existing

async def summarize_all_to_structured_json(input_dir: Path, output_path: Path):
    """Main function to process all documents and generate structured summaries"""
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Load all documents
    all_text = load_all_docs(input_dir)
    schema_str = json.dumps(full_summary_schema, indent=2)

    print("\U0001f9e0 Processing documents for module identification...")

    # Calculate optimal chunk size for processing
    total_tokens = len(tokenizer.encode(all_text))
    max_input_tokens = get_optimal_chunk_size(total_tokens, model=MODEL_NAME)
    print(f"[Chunking] Total tokens: {total_tokens}, max_input_tokens: {max_input_tokens}")

    # First pass: Identify all modules
    module_summaries = await run_prompt(
        chat=chat,
        user_message=all_text,
        model=MODEL_NAME,
        tokenizer=tokenizer,
        max_input_tokens=max_input_tokens,
        parse_response=parse_module_list,
        get_system_prompt=lambda i, total: get_clarifier_prompt(all_text, schema_str, i, total)
    )

    # Aggregate module summaries
    aggregated = {}
    for module in module_summaries:
        name = module.get("module", "UnknownModule")
        if name not in aggregated:
            aggregated[name] = module
        else:
            aggregated[name] = merge_module_summaries(aggregated[name], module)

    # Second pass: Enhance each module with RAG context
    print("\U0001f9e0 Enhancing module summaries with RAG context...")
    for name, base_summary in aggregated.items():
        # Get relevant context for this module
        context = embedding_retrieve(name, all_text)
        
        # Generate enhanced summary with RAG context
        enhanced_summary = await run_prompt(
            chat=chat,
            user_message=context,
            model=MODEL_NAME,
            tokenizer=tokenizer,
            max_input_tokens=max_input_tokens,
            parse_response=lambda x: parse_module_list(x)[0],  # Take first item since we're processing one module
            get_system_prompt=lambda i, total: f"""You are a senior software architect assistant.
Analyze the following context about the module '{name}' and enhance/validate the existing summary.
Use this schema:
{schema_str}

Current summary:
{json.dumps(base_summary, indent=2)}

Context:
{context}

Output a single JSON object with the enhanced summary. Keep existing correct information, add missing details, and fix any inaccuracies.
Only output valid JSON, no explanation or extra text."""
        )
        
        # Merge enhanced summary back
        aggregated[name] = merge_module_summaries(base_summary, enhanced_summary)

    # Save individual module summaries
    for name, data in aggregated.items():
        mod_dir = output_path / name
        mod_dir.mkdir(parents=True, exist_ok=True)
        with open(mod_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\u2705 Module '{name}' summary saved to {mod_dir/'full_summary.json'}")

    return aggregated 