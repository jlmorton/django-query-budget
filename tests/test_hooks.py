import threading
import time
import pytest

def test_hook_mode_enum():
    from django_query_budget.hooks import HookMode
    assert HookMode.SYNC.value == "sync"
    assert HookMode.ASYNC.value == "async"

def test_register_hook_default_async():
    from django_query_budget.hooks import HookMode, _registry, register_hook
    called = []
    def my_hook(**kwargs): called.append(kwargs)
    register_hook("on_query_executed", my_hook)
    entries = [e for e in _registry["on_query_executed"] if e[0] is my_hook]
    assert len(entries) == 1
    assert entries[0][1] == HookMode.ASYNC

def test_register_hook_explicit_sync():
    from django_query_budget.hooks import HookMode, _registry, register_hook
    def my_sync_hook(**kwargs): pass
    register_hook("on_query_executed", my_sync_hook, mode=HookMode.SYNC)
    entries = [e for e in _registry["on_query_executed"] if e[0] is my_sync_hook]
    assert entries[0][1] == HookMode.SYNC

def test_fire_sync_hooks():
    from django_query_budget.hooks import HookMode, fire_hooks, register_hook
    results = []
    def sync_hook(**kwargs): results.append(kwargs)
    register_hook("test_sync_event", sync_hook, mode=HookMode.SYNC)
    fire_hooks("test_sync_event", data="hello")
    assert len(results) == 1
    assert results[0]["data"] == "hello"

def test_fire_async_hooks():
    from django_query_budget.hooks import HookMode, fire_hooks, register_hook
    event = threading.Event()
    results = []
    def async_hook(**kwargs):
        results.append(kwargs)
        event.set()
    register_hook("test_async_event", async_hook, mode=HookMode.ASYNC)
    fire_hooks("test_async_event", value=42)
    assert event.wait(timeout=2.0)
    assert len(results) == 1
    assert results[0]["value"] == 42

def test_hook_exception_does_not_propagate(caplog):
    import logging
    from django_query_budget.hooks import HookMode, fire_hooks, register_hook
    def bad_hook(**kwargs): raise RuntimeError("hook error")
    register_hook("test_error_event", bad_hook, mode=HookMode.SYNC)
    with caplog.at_level(logging.ERROR, logger="django.query_budget.hooks"):
        fire_hooks("test_error_event")
    assert "hook error" in caplog.text

def test_base_hook_class():
    from django_query_budget.hooks import BaseHook, HookMode
    class MyHook(BaseHook):
        mode = HookMode.SYNC
        def __call__(self, **kwargs): self.called_with = kwargs
    hook = MyHook()
    assert hook.mode == HookMode.SYNC

def test_queue_overflow_drops_events():
    from django_query_budget.hooks import HookWorker
    worker = HookWorker(max_queue_size=2)
    worker.start()
    blocker = threading.Event()
    started = threading.Event()
    def slow_hook(**kwargs):
        started.set()
        blocker.wait(timeout=5.0)
    worker.enqueue(slow_hook, {})
    started.wait(timeout=2.0)
    worker.enqueue(slow_hook, {})
    worker.enqueue(slow_hook, {})
    dropped = worker.enqueue(slow_hook, {})
    assert dropped is False
    assert worker.dropped_count >= 1
    blocker.set()
    worker.stop()
