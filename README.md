# scripts v0.1.0

A minimalistic submodule assisting task analysis, dashboard update, context aggregation for LLM, and file redaction.

## Table of Contents

- [scripts v0.1.0](#scripts-v010)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Usage](#usage)
    - [Task Retrieval](#task-retrieval)
    - [Context Aggregation for LLMs](#context-aggregation-for-llms)
    - [File Redaction](#file-redaction)
    - [Redacted Git Diffs](#redacted-git-diffs)
  - [License](#license)

## Prerequisites

The scripts require Python 3.10+. To parse Markdown into AST, the scripts rely on `mistune`, a dependency-free Markdown parser. Aside from that, there are no other dependencies.

## Setup

```bash
git submodule add https://github.com/hnthap/scripts.git scripts/

pip install -r scripts/requirements.txt
```

## Usage

### Task Retrieval

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

### Context Aggregation for LLMs

To bundle your project files into a single, well-formatted Markdown file optimized for Large Language Models (like NotebookLM), use the `context` script. It automatically respects `.gitignore` rules and generates a directory tree.

```bash
python -m scripts.context "src/**/*.py" "README.md" --output temp/context.md
```

You can optionally specify the target LLM reader (defaults to `notebooklm`):

```bash
python -m scripts.context "scripts/**/*.py" --reader notebooklm
```

### File Redaction

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

### Redacted Git Diffs

To safely share your repository's recent changes without exposing sensitive credentials, use the `diff` script. This tool automatically captures your current `git diff` (including newly created, untracked files) and immediately passes it through the redaction engine.

```bash
python -m scripts.diff --secrets secrets.json
```

By default, the script assumes you are running it from the root of your Git repository and saves the outputs to a `temp/` directory. You can customize the paths using optional arguments:

```bash
python -m scripts.diff \
  --git-root /path/to/repo \
  --temp-diff temp/raw_snapshot.diff \
  --out-diff temp/safe_shareable.diff \
  --secrets secrets.json
```

## License

See [LICENSE](./LICENSE) for details.
