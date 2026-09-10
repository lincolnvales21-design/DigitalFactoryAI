import asyncio
import logging
import os
from datetime import datetime, timezone

from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator,
)

logger = logging.getLogger("digitalfactory.autonomous_runtime")


class AutonomousRuntime:

    def __init__(self):
        self.enabled = (
            os.getenv(
                "DIGITALFACTORY_AUTONOMOUS_ENABLED",
                "true",
            ).lower()
            in {"1", "true", "yes", "on"}
        )

        self.interval_seconds = int(
            os.getenv(
                "DIGITALFACTORY_AUTONOMOUS_INTERVAL",
                "900",
            )
        )

        self._task = None
        self._running = False
        self._cycle_lock = asyncio.Lock()
        self.last_cycle = None
        self.last_error = None
        self.cycles_completed = 0
        self.cycles_failed = 0

    async def run_once(self):

        if self._cycle_lock.locked():
            return {
                "status": "busy",
                "executed": False,
            }

        async with self._cycle_lock:

            started_at = datetime.now(
                timezone.utc
            ).isoformat()

            self.last_cycle = started_at
            self.last_error = None

            logger.warning(
                "DIGITALFACTORY AUTONOMOUS CYCLE STARTED"
            )

            try:
                result = await (
                    autonomous_cycle_orchestrator.run_cycle()
                )

                self.cycles_completed += 1

                logger.warning(
                    "DIGITALFACTORY AUTONOMOUS CYCLE FINISHED"
                )

                return result

            except Exception as exc:

                self.cycles_failed += 1
                self.last_error = str(exc)

                logger.exception(
                    "ERRO NO CICLO AUTONOMO"
                )

                return {
                    "status": "failed",
                    "executed": False,
                    "reason": str(exc),
                }

    async def _loop(self):

        self._running = True

        logger.warning(
            "DIGITALFACTORY AUTONOMOUS RUNTIME ONLINE"
        )

        while self._running:

            try:
                await self.run_once()

            except Exception as exc:

                self.last_error = str(exc)
                self.cycles_failed += 1

                logger.exception(
                    "ERRO FATAL PROTEGIDO NO RUNTIME"
                )

            if not self._running:
                break

            try:
                await asyncio.sleep(
                    self.interval_seconds
                )

            except asyncio.CancelledError:
                break

        self._running = False

        logger.warning(
            "DIGITALFACTORY AUTONOMOUS RUNTIME OFFLINE"
        )

    def start(self):

        if self._task is not None:
            if not self._task.done():
                return

        self._running = True

        self._task = asyncio.create_task(
            self._loop(),
            name="digitalfactory-autonomous-runtime",
        )

        logger.warning(
            "DIGITALFACTORY AUTONOMOUS RUNTIME TASK CREATED"
        )

    async def stop(self):

        self._running = False

        if self._task is not None:

            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._task = None

    def status(self):

        task_active = (
            self._task is not None
            and not self._task.done()
        )

        return {
            "enabled": self.enabled,
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "task_active": task_active,
            "cycles_completed": self.cycles_completed,
            "cycles_failed": self.cycles_failed,
            "last_cycle": self.last_cycle,
            "last_error": self.last_error,
        }


autonomous_runtime = AutonomousRuntime()
