import asyncio
from pathlib import Path

from clarifier.v2.summarizer_v2 import summarize_all_to_structured_json
from clarifier.validate_full_summary import validate_full_summary

async def run_pipeline():
    input_dir = Path("data/input")
    output_dir = Path("data/output/modules")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 只需调用一次，分析所有文档
    await summarize_all_to_structured_json(input_dir, output_dir)

    print("\n✅ Pipeline complete. Validating results...")
    for summary_file in output_dir.rglob("full_summary.json"):
        validate_full_summary(summary_file)

if __name__ == "__main__":
    asyncio.run(run_pipeline())