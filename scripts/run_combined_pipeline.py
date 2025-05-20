import asyncio
from pathlib import Path

from clarifier.summarizer_combined import summarize_all_to_structured_json
from clarifier.validate_full_summary import validate_full_summary
from clarifier.index_generator import generate_summary_index

async def run_pipeline():
    """Run the combined pipeline that uses both V1 and V2 features"""
    # Set up paths
    input_dir = Path("data/input")
    output_dir = Path("data/output/combined_modules")
    summary_index_path = Path("data/output/combined_summary_index.json")

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_index_path.parent.mkdir(parents=True, exist_ok=True)

    print("🚀 Starting combined pipeline...")
    print("📂 Input directory:", input_dir)
    print("📂 Output directory:", output_dir)

    # Process all documents and generate structured summaries
    await summarize_all_to_structured_json(input_dir, output_dir)

    # Generate summary index
    print("\n📑 Generating summary index...")
    generate_summary_index(output_dir, summary_index_path)

    # Validate all summaries
    print("\n🔍 Validating generated summaries...")
    validation_results = []
    for summary_file in output_dir.rglob("full_summary.json"):
        result = validate_full_summary(summary_file)
        validation_results.append((summary_file, result))

    # Report validation results
    print("\n📊 Validation Results:")
    all_valid = True
    for file_path, is_valid in validation_results:
        module_name = file_path.parent.name
        status = "✅" if is_valid else "❌"
        print(f"{status} {module_name}")
        if not is_valid:
            all_valid = False

    if all_valid:
        print("\n🎉 Pipeline completed successfully! All summaries are valid.")
    else:
        print("\n⚠️  Pipeline completed with validation errors. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(run_pipeline()) 