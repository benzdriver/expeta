# clarifier/vector_builder.py

import asyncio
from pathlib import Path
from memory.client_factory import get_embedding_client

INPUT_DIR = Path("data/input")

def find_markdown_files(path: Path):
    return list(path.glob("*.md"))

async def build_vector_database():
    files = find_markdown_files(INPUT_DIR)
    if not files:
        print("❌ No .md files found in data/input. Please add your architecture documents.")
        return

    print(f"📄 Found {len(files)} markdown files. Embedding...")
    client = get_embedding_client()
    client.build(files)
    print("✅ Vector database built successfully.")

if __name__ == "__main__":
    asyncio.run(build_vector_database())
