# File: backend/core/scheduler.py
import asyncio
import contextlib
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, Optional

with contextlib.suppress(Exception):
    from jobs.world_pulse_jobs import run_daily_world_pulse, run_weekly_rollup  # type: ignore[misc]

UTC = timezone.utc

class TaskHandle:
    def __init__(self, name: str, coro_factory: Callable[[], Awaitable[None]]):
        self.name = name
        self._coro_factory = coro_factory
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def start(self):
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._runner(), name=self.name)

    async def stop(self):
        self._stop.set()
        if self._task:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._task, timeout=3)

    async def _runner(self):
        try:
            await self._coro_factory()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Scheduler] Task {self.name} crashed: {e!r}")

class SimpleScheduler:
    def __init__(self):
        self._handles: list[TaskHandle] = []

    def every(self, seconds: int, name: str, func: Callable[[], Awaitable[None]]):
        async def _job():
            while True:
                await func()
                await asyncio.sleep(seconds)
        handle = TaskHandle(name=name, coro_factory=_job)
        self._handles.append(handle)
        return handle

    def daily_at(self, hour: int, minute: int, name: str, func: Callable[[], Awaitable[None]]):
        async def _job():
            while True:
                now = datetime.now(UTC)
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                await asyncio.sleep((target - now).total_seconds())
                await func()
        handle = TaskHandle(name=name, coro_factory=_job)
        self._handles.append(handle)
        return handle

    def weekly_at(self, dow: int, hour: int, minute: int, name: str, func: Callable[[], Awaitable[None]]):
        async def _job():
            while True:
                now = datetime.now(UTC)
                days_ahead = (dow - now.weekday()) % 7
                target = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=7)
                await asyncio.sleep((target - now).total_seconds())
                await func()
        handle = TaskHandle(name=name, coro_factory=_job)
        self._handles.append(handle)
        return handle

    async def start(self):
        for h in self._handles:
            await h.start()

    async def stop(self):
        for h in self._handles:
            await h.stop()

scheduler = SimpleScheduler()

async def _noop():
    pass

try:
    scheduler.daily_at(2, 0, name="world_pulse_daily", func=run_daily_world_pulse)  # type: ignore[name-defined]
except Exception:
    scheduler.daily_at(2, 0, name="world_pulse_daily_noop", func=_noop)

try:
    scheduler.weekly_at(0, 3, 0, name="world_pulse_weekly", func=run_weekly_rollup)  # type: ignore[name-defined]
except Exception:
    scheduler.weekly_at(0, 3, 0, name="world_pulse_weekly_noop", func=_noop)

async def lifespan(app):
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
