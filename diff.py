import argparse
import subprocess
import sys
from pathlib import Path
from typing import Self, override

from scripts.cli import ArgumentConfig
from scripts.redact import redact_file


class GitDiffConfig(ArgumentConfig):
    git_root: Path = Path.cwd()
    temp_diff: Path = Path("temp/a.diff")
    out_diff: Path = Path("temp/a.diff")
    secrets: Path = Path()  # Dummy value for a mandatory field

    @classmethod
    @override
    def parse_args(cls) -> "Self":
        parser = argparse.ArgumentParser(
            description="Generate a git diff and apply redaction rules."
        )

        _ = parser.add_argument(
            "--git-root",
            type=Path,
            help="Root of the git repo (default: current directory).",
        )

        _ = parser.add_argument(
            "--temp-diff",
            type=Path,
            help="Path to save the raw diff (default: temp/temp.diff).",
        )

        _ = parser.add_argument(
            "--out-diff",
            type=Path,
            help="Path to save the redacted diff (default: temp/a.diff).",
        )

        _ = parser.add_argument(
            "--secrets",
            type=Path,
            required=True,
            help="Path to the JSON file containing redaction instructions.",
        )

        args = parser.parse_args(namespace=cls())

        # Resolve paths
        args.git_root = args.git_root.resolve()
        args.temp_diff = args.temp_diff.resolve()
        args.out_diff = args.out_diff.resolve()
        args.secrets = args.secrets.resolve()

        if not args.secrets.is_file():
            parser.error(f"Secrets file not found: {args.secrets}")

        # Ensure output directories exist
        args.temp_diff.parent.mkdir(parents=True, exist_ok=True)
        args.out_diff.parent.mkdir(parents=True, exist_ok=True)

        return args


def main():
    args = GitDiffConfig.parse_args()

    try:
        _ = subprocess.run(
            ["git", "add", "--intent-to-add", "."],
            cwd=args.git_root,
            check=True,
            capture_output=True,  # Keeps the terminal clean
        )

        with open(args.temp_diff, "w", encoding="utf-8") as f:
            _ = subprocess.run(
                ["git", "diff"],
                cwd=args.git_root,
                stdout=f,
                check=True,
            )

    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Git executable not found. Ensure git is installed.")
        sys.exit(1)

    redact_file(args.temp_diff, args.secrets, args.out_diff)


if __name__ == "__main__":
    main()
