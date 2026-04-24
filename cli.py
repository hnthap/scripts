"""
File: scripts/cli.py

A package providing CLI utilities.
"""

import argparse
import re
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Self, override


class ArgumentConfig(ABC, argparse.Namespace):
    @classmethod
    @abstractmethod
    def parse_args(cls) -> "Self":
        pass


class TaskRelatedConfig(ArgumentConfig):
    project_name: str = ""  # Dummy value for a mandatory field
    start_md: Path = Path(__file__).parent.parent / "README.md"
    target_pattern: re.Pattern[str] = re.compile(r"notes/\d+\_.*\.md")
    date_range: tuple[date, date] | None = None

    @classmethod
    @override
    def parse_args(cls):
        parser = argparse.ArgumentParser(
            description="Extract and track tasks from Markdown logs."
        )

        _ = parser.add_argument(
            "--project-name",
            dest="project_name",
            required=True,
            help="Name of the project.",
        )

        _ = parser.add_argument(
            "--start-md",
            dest="start_md",
            type=Path,
            help="Path to the starting Markdown file.",
        )

        _ = parser.add_argument(
            "--target-pattern",
            dest="target_pattern",
            help="Regex pattern to match target paths.",
        )

        _ = parser.add_argument(
            "--date-range",
            dest="date_range",
            nargs=2,
            type=date.fromisoformat,
            metavar=(
                "START_DATE",
                "END_DATE",
            ),
            help="Optional start and end dates (YYYY-MM-DD) to filter tasks.",
        )

        args = parser.parse_args(namespace=cls())

        args.start_md = args.start_md.resolve()
        if not args.start_md.is_file():
            parser.error(
                f"The starting Markdown file does not exist: {args.start_md}"
            )

        args.target_pattern = re.compile(args.target_pattern)

        if args.date_range is not None:
            start_date, end_date = args.date_range
            if start_date > end_date:
                parser.error(
                    f"Invalid date range: Start date ({start_date}) "
                    + f"cannot be after the end date ({end_date})."
                )

        return args


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


class ContextConfig(ArgumentConfig):
    files: list[str] = []  # Dummy value for a mandatory field
    output: Path = Path("temp/context.md")
    reader: str = "notebooklm"

    @classmethod
    @override
    def parse_args(cls) -> "Self":
        parser = argparse.ArgumentParser(
            description="Concatenate scripts for LLM context."
        )

        _ = parser.add_argument(
            "files", nargs="+", help="File paths or glob patterns to include."
        )

        _ = parser.add_argument(
            "--output",
            dest="output",
            type=Path,
            help="Output file path.",
        )

        _ = parser.add_argument(
            "--reader",
            dest="reader",
            type=str,
            help="Target reader (LLM).",
        )

        args = parser.parse_args(namespace=cls())

        args.output = args.output.resolve()
        args.output.parent.mkdir(parents=True, exist_ok=True)

        return args
