"""
File: scripts/dashboard.py

A script generating a simple task dashboard in the terminal.
"""

from datetime import date

from scripts.tasks import Document, DocumentTree, TaskRelatedConfig, TaskStatus


def main():
    args = TaskRelatedConfig.parse_args()

    documents = DocumentTree(args.start_md).collect_documents()

    targeted_documents: list[Document] = []
    for document in documents:
        if not args.target_pattern.search(document.path.resolve().as_posix()):
            continue

        document = document.parse()
        if document.num_tasks > 0:
            targeted_documents.append(document)

    if targeted_documents:
        print_dashboard(targeted_documents, args.date_range)
    else:
        print("\nNo tasks found matching the criteria.\n")


def print_dashboard(
    documents: list["Document"], date_range: tuple[date, date] | None = None
):
    total_tasks = 0
    status_counts = {
        TaskStatus.DONE: 0,
        TaskStatus.FAILED: 0,
        TaskStatus.PENDING: 0,
    }

    # Aggregate data
    for doc in documents:
        # Filter tasks as they are generated
        for task in (
            t
            for t in doc.iter_tasks()
            if not date_range
            or (
                t.completion_date
                and date_range[0] <= t.completion_date <= date_range[1]
            )
        ):
            total_tasks += 1
            status_counts[task.status] += 1

    done = status_counts[TaskStatus.DONE]
    failed = status_counts[TaskStatus.FAILED]
    pending = status_counts[TaskStatus.PENDING]

    # Both Done and Failed are terminal states
    resolved = done + failed
    progress_rate = (resolved / total_tasks * 100) if total_tasks else 0

    # Print Header
    print("\n" + "=" * 60)
    print(" 📊 TASK TRACKING DASHBOARD")
    print("=" * 60)

    # Print Global Metrics
    print("\n📈 GLOBAL METRICS")
    print(f"   Total Tasks: {total_tasks}")
    print(f"   Resolved:    {resolved} ({progress_rate:.1f}%)")
    print(f"     ├── Done:   {done}")
    print(f"     └── Failed: {failed}")
    print(f"   Pending:     {pending}")

    # Print Visual Progress Bar
    bar_length = 40
    done_filled = int(bar_length * done // total_tasks) if total_tasks else 0
    failed_filled = (
        int(bar_length * failed // total_tasks) if total_tasks else 0
    )
    pending_empty = bar_length - done_filled - failed_filled

    # █ = Done, ▓ = Failed (Terminal), ░ = Pending
    bar = "█" * done_filled + "▓" * failed_filled + "░" * pending_empty
    print(f"\n   Progress: |{bar}|")

    # Print File Breakdown
    print("\n📁 BREAKDOWN BY FILE")
    for doc in documents:
        # 1. Apply the same date filter to the local file tasks
        doc_tasks = [
            t
            for t in doc.iter_tasks()
            if not date_range
            or (
                t.completion_date
                and date_range[0] <= t.completion_date <= date_range[1]
            )
        ]

        # 2. Skip files that have no tasks in this date range
        if not doc_tasks:
            continue

        doc_done = sum(1 for t in doc_tasks if t.status == TaskStatus.DONE)
        doc_failed = sum(1 for t in doc_tasks if t.status == TaskStatus.FAILED)
        doc_pending = sum(
            1 for t in doc_tasks if t.status == TaskStatus.PENDING
        )

        # A file is fully clear if nothing is pending
        status_indicator = "✅" if doc_pending == 0 and doc_done != 0 else "⏳"

        print(
            f"   {status_indicator} {doc.path.name}: "
            + f"{doc_pending} pending "
            + f"({doc_done} done, {doc_failed} failed)"
        )

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
