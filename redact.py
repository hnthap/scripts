"""
File: scripts/redact.py

A script redacts a specific text-based file.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import override

from scripts.cli import ArgumentConfig


def main():
    args = RedactionConfig.parse_args()
    redact_file(args.input, args.secrets, args.output)


class RedactionConfig(ArgumentConfig):
    input: Path = Path()  # Dummy value for a mandatory field
    secrets: Path = Path()  # Dummy value for a mandatory field
    output: Path = Path()  # Dummy value for a mandatory field

    @classmethod
    @override
    def parse_args(cls):
        parser = argparse.ArgumentParser(
            description="Redact secrets from a target input file."
        )

        _ = parser.add_argument(
            "--input",
            required=True,
            type=Path,
            help="Path to the file that needs to be redacted.",
        )

        _ = parser.add_argument(
            "--secrets",
            required=True,
            type=Path,
            help="Path to the JSON file containing secrets to redact.",
        )

        _ = parser.add_argument(
            "--output",
            required=True,
            type=Path,
            help="Filename for the redacted file.",
        )

        args = parser.parse_args(namespace=cls())

        args.input = args.input.resolve()
        if not args.input.is_file():
            parser.error(f"Input file not found: {args.input}")

        args.secrets = args.secrets.resolve()
        if not args.secrets.is_file():
            parser.error(f"Secrets JSON file not found: {args.secrets}")

        args.output = args.output.resolve()
        args.output.parent.mkdir(parents=True, exist_ok=True)

        return args


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
