def get_clarifier_prompt(doc_text: str, schema: str, chunk_idx: int = None, total_chunks: int = None) -> str:
    chunk_info = ""
    if chunk_idx is not None and total_chunks is not None:
        chunk_info = f"This is chunk {chunk_idx} of {total_chunks} of the full document set. Only analyze the content in this chunk. After all chunks are processed, the results will be merged.\n\n"
    return f"""You are a senior full-stack software architect assistant.

{chunk_info}You will receive multiple design and code documents, each separated by a header like '### FILE: filename.md ###'.
Analyze ALL documents together and extract ALL software modules described, including but not limited to:
- Business domains (e.g. Auth, Profile, Dashboard, Forms, etc.)
- All services, controllers, repositories, utilities, test modules, integration tests, configuration modules, and any other implementation units.

For each discovered module, output a JSON object strictly following this schema:
{schema}

If a module is a submodule (e.g. a service, controller, repository, or test), fill in as much detail as possible, and indicate its parent module if applicable.

If any field is missing, use null or an empty list. If you are unsure, make a best guess based on the context.

Output a JSON array, where each element is a module (including submodules and implementation units). Do not output any explanation, markdown, or extra text.

--- DOCUMENT START ---
{doc_text}
--- DOCUMENT END ---
"""