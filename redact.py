"""
File: scripts/redact.py

A script redacts a specific text-based file.
"""

import json
import sys
from pathlib import Path

from scripts.cli import RedactionConfig


def main():
    args = RedactionConfig.parse_args()
    redact_file(args.input, args.secrets, args.output)


def redact_file(input_path: Path, secrets_path: Path, output_path: Path):
    # 1. Read the input file
    target_text = input_path.read_text("utf-8")

    # 2. Read the JSON file for secrets
    try:
        redaction_rules: list[dict[str, str]] = json.loads(  # pyright: ignore[reportAny]
            secrets_path.read_text("utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading secrets file: {e}")
        sys.exit(1)

    # 3. Redact the secrets found in the target text
    redacted_text = target_text
    for rule in redaction_rules:
        secret = rule.get("secret")
        replacement = rule.get("replaced_with", "[REDACTED]")
        if secret:
            redacted_text = redacted_text.replace(secret, replacement)

    # 4. Produce a redacted output file
    try:
        _ = output_path.write_text(redacted_text, encoding="utf-8")
        print(f"Redacted file saved to: {output_path}")
    except OSError as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
