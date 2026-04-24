"""
File: scripts/core.py

The core package defining necessary types, methods, and classes for other
scripts.

This package requires `mistune`, a dependency-free Markdown parser.
"""

import enum
import re
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Generator
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import ClassVar, Self, override

import mistune
from mistune.core import BlockState
from mistune.renderers.markdown import MarkdownRenderer

RawTree = dict[str, "str | RawTree | list[RawTree]"]

parse_markdown = mistune.create_markdown(renderer="ast")

_markdown_renderer = MarkdownRenderer()


def render_markdown(tokens: list[RawTree]):
    return _markdown_renderer(tokens, BlockState())


@dataclass
class Bullet:
    text: str
    children: list["Bullet"] = field(default_factory=list)


class Parsable(ABC):
    @abstractmethod
    def parse(self, *args, **kwargs) -> "Self":  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        pass


class TaskStatus(enum.Enum):
    DONE = 1
    FAILED = 2
    PENDING = 3

    @classmethod
    def from_text(cls, text: str) -> "TaskStatus":
        text = text.strip().lower()
        if text == "x":
            return cls.DONE
        if "failed" in text:
            return cls.FAILED
        return cls.PENDING


@dataclass
class Task:
    status: TaskStatus
    no: int | None
    completion_date: date | None
    detail: str

    _task_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\[(?P<status>\*\*FAILED\*\*|[xX]|\s+)\]\s*"
        + r"(?:(?P<no>\d+)\.\s*)?"
        + r"(?:(?P<year>\d{4})\-(?P<month>\d{2})\-(?P<day>\d{2})[:\s]*)?"
        + r"(?P<detail>[^\n]*)"
    )

    @override
    def __str__(self) -> str:
        s = ""
        if self.status == TaskStatus.DONE:
            s += "[x] "
        elif self.status == TaskStatus.FAILED:
            s += "~F~ "
        else:
            s += "[ ] "
        if self.no is not None:
            s += f"{self.no:>2}. "
        if self.completion_date is not None:
            s += f"[ {self.completion_date.strftime('%Y-%m-%d')} ] "
        s += self.detail
        return s

    @classmethod
    def from_text(cls, text: str) -> "Task | None":
        m = cls._task_pattern.search(text)
        if m is None:
            return None

        data = m.groupdict()

        completion_date: date | None = None
        if (
            data["year"] is not None
            and data["month"] is not None
            and data["day"] is not None
        ):
            completion_date = date(
                int(str(data["year"])),
                int(str(data["month"])),
                int(str(data["day"])),
            )

        return Task(
            status=TaskStatus.from_text(str(data["status"])),
            no=int(data["no"]) if data["no"] is not None else None,
            completion_date=completion_date,
            detail=str(data["detail"]),
        )

    @classmethod
    def from_parsed_markdown(cls, token: RawTree) -> "Task | None":
        tokens = [{**token, "type": "paragraph"}]
        return cls.from_text(render_markdown(tokens))


@dataclass
class Document(Parsable):
    path: Path

    _tasks: list[Task] = field(default_factory=list)

    @property
    def num_tasks(self) -> int:
        return len(self._tasks)

    def iter_tasks(self) -> Generator[Task, None, None]:
        for task in self._tasks:
            yield deepcopy(task)

    @override
    def __str__(self) -> str:
        return f"'{self.path.resolve().as_posix()}'"

    @override
    def __repr__(self) -> str:
        return f"Document('{self.path.resolve().as_posix()}')"

    @override
    def __hash__(self) -> int:
        return hash(self.path.resolve())

    @override
    def parse(self) -> "Document":
        parsed: str | list[RawTree] = parse_markdown(
            self.path.read_text("utf-8")
        )

        if isinstance(parsed, str):
            raise RuntimeError(
                "Failed to parse Document at "
                + f"{self.path.resolve().as_posix()} with mistune."
            )

        tasks: list[Task] = []
        queue = deque(parsed)

        while queue:
            item = queue.popleft()

            if item.get("type") == "list":
                for child in item.get("children", []):
                    if (
                        isinstance(child, dict)
                        and child.get("type") == "list_item"
                    ):
                        task = Task.from_parsed_markdown(child)
                        if task:
                            tasks.append(task)

            # Tasks are always first-level bullets,
            # so it is not necessary to traverse down the tree.

        self._tasks = tasks
        return self


@dataclass
class DocumentTree(Parsable):
    root_md: Path
    _children: list["DocumentTree"] = field(default_factory=list, init=False)
    _cache: ClassVar[dict[Path, "DocumentTree"]] = {}

    def __len__(self) -> int:
        return len(self._children)

    def __getitem__(self, idx: int) -> "DocumentTree":
        return self._children[idx]

    def iter_children(self) -> Generator["DocumentTree", None, None]:
        yield from self._children

    @override
    def __str__(self) -> str:
        return f"'{self.root_md.as_posix()}'"

    @override
    def __repr__(self) -> str:
        return f"DocumentTree('{self.root_md.as_posix()}')"

    @override
    def parse(self, *, force: bool = False) -> "DocumentTree":
        if not force and self.root_md in self._cache:
            return self

        parsed: str | list[RawTree] = parse_markdown(
            self.root_md.read_text("utf-8")
        )

        if isinstance(parsed, str):
            raise RuntimeError(
                "Failed to parse DocumentTree at "
                + f"{self.root_md.resolve().as_posix()} with mistune."
            )

        children: list[DocumentTree] = []
        queue = deque(parsed)
        root_dir = self.root_md.parent

        while queue:
            item = queue.popleft()

            if (
                item.get("type") == "link"
                and "attrs" in item
                and isinstance(item["attrs"], dict)
                and isinstance(item["attrs"]["url"], str)
            ):
                href = item["attrs"]["url"]
                path = (root_dir / href).resolve()
                if path.is_file() and path.suffix.lower() == ".md":
                    children.append(DocumentTree(path))

            if "children" in item and isinstance(item["children"], list):
                queue.extend(item["children"])

        self._children = children

        self._cache[self.root_md] = self

        return self

    def root_as_document(self) -> Document:
        return Document(self.root_md)

    def collect_documents(
        self, *, pattern: re.Pattern[str] | None = None
    ) -> list[Document]:
        tree_queue: deque[DocumentTree] = deque([self])
        documents: list[Document] = []
        traversed: set[Document] = set()

        while tree_queue:
            tree = tree_queue.popleft()
            document = tree.root_as_document()

            if document in traversed:
                continue

            traversed.add(document)

            if not pattern or pattern.search(
                document.path.resolve().as_posix()
            ):
                documents.append(document)

            tree = tree.parse()
            for child in tree.iter_children():
                tree_queue.append(child)

        return documents
