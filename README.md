# Expeta

Expeta is a code analysis and summarization system that uses LLMs to extract and organize information from codebases.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Input Data

Place your input documents (markdown files) in the `data/input` directory.

## Running the Pipelines

### Clarifier V2 (Recommended)

The latest version uses improved entity discovery and RAG retrieval:

```bash
python -m clarifier_v2.smart_pipeline
```

Alternatively, specify custom input and output directories:

```bash
python -m clarifier_v2.smart_pipeline path/to/input path/to/output
```

### Combined Pipeline

Runs a pipeline that combines features from both V1 and V2:

```bash
python scripts/run_combined_pipeline.py
```

### Original Clarifier

Run the original clarifier implementation:

```bash
python run_clarifier.py
```

## Output

The system will generate:

- Structured module summaries in `data/output/v2/smart_modules/` (for clarifier_v2)
- Dependency relationships between modules
- A summary index for quick access to module information

## Features

- Document analysis and module identification
- Code structure summarization 
- Dependency graph generation and visualization
- RAG (Retrieval-Augmented Generation) capabilities