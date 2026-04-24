# scripts v0.1.0

A minimalistic submodule assisting task analysis, dashboard update, context aggregation for LLM, and file redaction.

## Table of Contents

- [scripts v0.1.0](#scripts-v010)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Usage: Task Retrieval](#usage-task-retrieval)
  - [Usage: Context Aggregation for LLMs](#usage-context-aggregation-for-llms)
  - [Usage: File Redaction](#usage-file-redaction)
- [License](#license)

## Prerequisites

The scripts require Python 3.10+. To parse Markdown into AST, the scripts rely on `mistune`, a dependency-free Markdown parser. Aside from that, there are no other dependencies.

## Setup

```bash
git submodule add https://github.com/hnthap/scripts.git scripts/

pip install -r scripts/requirements.txt
```

## Usage: Task Retrieval

Task JSON format:

```typescript
{
  project: string;
  document: string;
  status: "DONE" | "FAILED" | "PENDING";
  no: number | null;
  completion_date: string | null;  # "YYYY-MM-DD"
  detail: string;
}
```

To retrieve all tasks:

```bash
python -m scripts.tasks --project-name devops-training-log --start-md README.md
```

To see the task dashboard:

```bash
python -m scripts.dashboard --project-name devops-training-log --start-md README.md
```

## Usage: Context Aggregation for LLMs

To bundle your project files into a single, well-formatted Markdown file optimized for Large Language Models (like NotebookLM), use the `context` script. It automatically respects `.gitignore` rules and generates a directory tree.

```bash
python -m scripts.context "src/**/*.py" "README.md" --output temp/context.md
```

You can optionally specify the target LLM reader (defaults to `notebooklm`):

```bash
python -m scripts.context "scripts/**/*.py" --reader notebooklm
```

## Usage: File Redaction

To safely share text files or logs without exposing sensitive information, use the `redact` script. 

First, define your redaction rules in a JSON file (e.g., `secrets.json`):

```json
[
  {
    "secret": "YOUR_ACTUAL_API_KEY",
    "replaced_with": "[REDACTED_API_KEY]"
  },
  {
    "secret": "admin_password123",
    "replaced_with": "[REDACTED]"
  }
]
```

Then, run the script against your target file:
```bash
python -m scripts.redact --input path/to/raw_log.txt --secrets secrets.json --output path/to/safe_log.txt
```

# License

See [LICENSE](./LICENSE) for details.
