"""Pipeline: chain multiple log processing steps into a single pass."""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, List

LogEntry = dict
Step = Callable[[Iterable[LogEntry]], Iterator[LogEntry]]


class Pipeline:
    """Compose a sequence of processing steps that each consume and yield entries."""

    def __init__(self) -> None:
        self._steps: List[Step] = []

    def add_step(self, step: Step) -> "Pipeline":
        """Append a step and return self for chaining."""
        self._steps.append(step)
        return self

    def run(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Pass *entries* through every step in order."""
        stream: Iterable[LogEntry] = entries
        for step in self._steps:
            stream = step(stream)
        yield from stream

    def __len__(self) -> int:
        return len(self._steps)


def make_filter_step(predicate: Callable[[LogEntry], bool]) -> Step:
    """Wrap a boolean predicate as a pipeline step."""

    def _step(entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        for entry in entries:
            if predicate(entry):
                yield entry

    return _step


def make_transform_step(transform: Callable[[LogEntry], LogEntry]) -> Step:
    """Wrap a mapping function as a pipeline step."""

    def _step(entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        for entry in entries:
            yield transform(entry)

    return _step


def build_pipeline(steps: List[Step]) -> Pipeline:
    """Convenience constructor that adds all *steps* at once."""
    p = Pipeline()
    for step in steps:
        p.add_step(step)
    return p
