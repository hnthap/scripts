"""
File: scripts/tasks.py

A script prints all tasks in one JSON string.
"""

import json

from scripts.cli import TaskRelatedConfig
from scripts.core import DocumentTree


def main():
    args = TaskRelatedConfig.parse_args()

    target_root = args.start_md.parent

    documents = DocumentTree(args.start_md).collect_documents()

    data: list[dict[str, int | str | None]] = []

    documents = list(
        filter(
            lambda doc: args.target_pattern.search(
                doc.path.resolve().as_posix()
            ),
            documents,
        )
    )

    for document in documents:
        document = document.parse()

        if not document.num_tasks:
            continue

        try:
            document_relpath = (
                document.path.resolve().relative_to(target_root).as_posix()
            )
        except ValueError:
            document_relpath = document.path.resolve().as_posix()

        tasks = [
            {
                "project": args.project_name,
                "document": document_relpath,
                "status": task.status.name,
                "no": task.no,
                "completion_date": task.completion_date.strftime("%Y-%m-%d")
                if task.completion_date
                else None,
                "detail": task.detail,
            }
            for task in document.iter_tasks()
            if not args.date_range
            or (
                task.completion_date
                and args.date_range[0]
                <= task.completion_date
                <= args.date_range[1]
            )
        ]

        data.extend(tasks)

    print(json.dumps(data))


if __name__ == "__main__":
    main()
