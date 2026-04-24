"""
File: scripts/context.py

A script concatenating files into a single context file optimized for LLM
analysis.
"""

import argparse
import glob
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Self, override

from scripts.cli import ArgumentConfig

# Safety limits
MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", "-1"))
BINARY_EXTENSIONS = {
    ".7z",
    ".bin",
    ".exe",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".pyc",
    ".rar",
    ".tar",
    ".webp",
    ".zip",
}
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".c": "c",
    ".cc": "cpp",
    ".code-workspace": "json",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".c++": "cpp",
    ".css": "css",
    ".env": "bash",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".rs": "rust",
    ".sh": "bash",
    ".ts": "typescript",
    ".txt": "text",
    ".xml": "xml",
    ".yaml": "yaml",
}
IGNORED_FILES = {
    file for file in os.environ.get("IGNORED", "").split(";") if file
}


def main():
    args = ContextConfig.parse_args()

    # Expand globs for Windows compatibility
    files: list[Path] = []
    for pattern in args.files:
        matches = glob.glob(pattern, recursive=True) or [pattern]
        files.extend(map(Path, matches))

    # Filter .gitignore
    files = filter_gitignore(files)

    # Apply additional filters
    files = [f for f in files if not is_ignored(f)]

    # Remove duplicates and non-files
    files = sorted(set(f for f in files if f.is_file()), key=path_sorting_key)

    concatenate_scripts(files, Path(args.output), args.reader)


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


def filter_gitignore(files: list[Path]) -> list[Path]:
    if not files:
        return []

    file_str_list = [str(f.resolve()) for f in files]

    try:
        result = subprocess.run(
            ["git", "check-ignore", "--stdin", "-z"],
            input="\0".join(file_str_list) + "\0",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        ignored_paths = set(result.stdout.strip("\0").split("\0"))
        return [f for f in files if str(f.resolve()) not in ignored_paths]

    except FileNotFoundError:
        logging.warning("Git not found. Skipping .gitignore filtering.")
        return files

    except Exception as e:
        logging.warning(f"Git check-ignore failed ({e}). Returning all files.")
        return files


def is_ignored(path: Path) -> bool:
    name = path.name

    # Check IGNORED_FILES
    if any(name == f for f in IGNORED_FILES):
        return True

    # Check extension
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # Check size
    try:
        if MAX_FILE_SIZE > 0 and path.stat().st_size > MAX_FILE_SIZE:
            logging.warning(f"Skipping {path.as_posix()} (Too large)")
            return True
    except OSError:
        pass
    return False


def generate_tree(file_paths: list[Path]) -> str:
    """
    Generates a visual directory tree from a list of Path objects.
    Correctly includes parent directory names.
    """
    tree_lines = ["# PROJECT STRUCTURE", "```"]

    # Sort paths to ensure directories are grouped together,
    # prioritizing README files at every level.
    sorted_paths = sorted(file_paths, key=path_sorting_key)

    # Keep track of the previous path's parts to identify common parents
    previous_parts = ()

    for path in sorted_paths:
        current_parts = path.parts

        # Determine the index where the current path diverges
        # from the previous one
        common_depth = 0
        for p1, p2 in zip(previous_parts, current_parts, strict=False):
            if p1 != p2:
                break
            common_depth += 1

        # Print only the parts of the path that haven't been printed in this
        # branch yet
        for i in range(common_depth, len(current_parts)):
            indent = "    " * i
            part = current_parts[i]
            tree_lines.append(f"{indent}├── {part}")

        previous_parts = current_parts

    tree_lines.append("```")
    return "\n".join(tree_lines)


def get_language(file_path: Path):
    """Guess the markdown language tag based on extension."""
    ext = file_path.suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, "")


def calculate_fence(content: str) -> str:
    """
    Determines the number of backticks needed to wrap the content safely.
    Returns a string of backticks (e.g., "```" or "````").
    """
    # Find all sequences of backticks in the content
    matches: list[str] = re.findall(r"`+", content)

    # If no backticks found, return standard 3
    if not matches:
        return "```"

    # Find the longest sequence of backticks
    max_ticks = max(len(m) for m in matches)

    # Return max found + 1 (but at least 3)
    return "`" * max(3, max_ticks + 1)


def concatenate_scripts(
    files: list[Path], output_file: Path, reader: str
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as f:
            # 1. WRITE THE FILE LIST
            _ = f.write(generate_tree(files))

            # 2. WRITE THE FILES
            _ = f.write("\n\n# FILE CONTENTS\n\n")
            for i, file_path in enumerate(files):
                language = get_language(file_path)

                _ = f.write(f"## {file_path.as_posix()}\n")
                _ = f.write(f'[file path="{file_path.as_posix()}"]\n')

                content = ""
                read_success = False

                # Read content first so we can calculate fence length
                try:
                    content = file_path.read_text(
                        encoding="utf-8", errors="replace"
                    )

                    if not content.endswith("\n"):
                        content += "\n"
                    read_success = True
                except Exception as e:
                    logging.error(f"Error reading {file_path.as_posix()}: {e}")
                    content = f"!! ERROR READING FILE: {e} !!\n"

                # Dynamic Fencing Logic
                fence = (
                    "" if reader == "notebooklm" else calculate_fence(content)
                )

                _ = f.write(f"\n{fence}{language}\n")  # Opening fence
                _ = f.write(content)
                _ = f.write(f"{fence}\n")  # Closing fence
                _ = f.write("[end file]\n\n")

                if read_success:
                    logging.info(
                        f"[{i + 1}/{len(files)}] Added {file_path.as_posix()}"
                    )

        logging.info(f"Done. Output generated at: {output_file.as_posix()}")

    except Exception as e:
        logging.error(f"Failed to write output: {e}")


def path_sorting_key(p: Path) -> tuple[tuple[tuple[int, str], ...]]:
    return (
        tuple(
            (0, part) if part.upper().startswith("README") else (1, part)
            for part in p.parts
        ),
    )


if __name__ == "__main__":
    main()
