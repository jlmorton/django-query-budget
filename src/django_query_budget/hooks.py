from __future__ import annotations
import enum
import logging
import queue
import threading
from typing import Any, Callable

logger = logging.getLogger("django.query_budget.hooks")
HookCallable = Callable[..., None]


class ExecutionMode(enum.Enum):
    SYNC = "sync"
    ASYNC = "async"


# Backwards-compatible alias
HookMode = ExecutionMode


class BaseHook:
    mode: HookMode = HookMode.ASYNC

    def __call__(self, **kwargs: Any) -> None:
        raise NotImplementedError


class HookWorker:
    def __init__(self, max_queue_size: int = 10_000) -> None:
        self._queue: queue.Queue[tuple[HookCallable, dict] | None] = queue.Queue(maxsize=max_queue_size)
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()
        self.dropped_count = 0
        self._drop_lock = threading.Lock()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stopped.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="query-budget-hooks")
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def enqueue(self, hook: HookCallable, kwargs: dict) -> bool:
        try:
            self._queue.put_nowait((hook, kwargs))
            return True
        except queue.Full:
            with self._drop_lock:
                self.dropped_count += 1
            return False

    def _run(self) -> None:
        while not self._stopped.is_set():
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            if item is None:
                break
            hook, kwargs = item
            try:
                hook(**kwargs)
            except Exception:
                logger.exception("Async hook %s raised an exception", hook)


_registry: dict[str, list[tuple[HookCallable, HookMode]]] = {}
_worker: HookWorker | None = None
_worker_lock = threading.Lock()


def _get_worker() -> HookWorker:
    global _worker
    if _worker is None:
        with _worker_lock:
            if _worker is None:
                _worker = HookWorker()
                _worker.start()
    return _worker


def register_hook(event: str, hook: HookCallable, mode: HookMode = HookMode.ASYNC) -> None:
    if event not in _registry:
        _registry[event] = []
    _registry[event].append((hook, mode))


def fire_hooks(event: str, **kwargs: Any) -> None:
    hooks = _registry.get(event, [])
    for hook, mode in hooks:
        if mode == HookMode.SYNC:
            try:
                hook(**kwargs)
            except Exception:
                logger.exception("Sync hook %s raised an exception", hook)
        else:
            _get_worker().enqueue(hook, kwargs)
