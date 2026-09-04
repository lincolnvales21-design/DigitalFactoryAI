
import asyncio
from datetime import datetime
from pathlib import Path

from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator
)


class AutonomousSchedulerBridge:
    """
    Faz a ponte entre o Scheduler existente e o
    AutonomousCycleOrchestrator.

    O Scheduler continua responsável pelo intervalo.
    Este componente garante que cada disparo execute
    um ciclo autônomo completo.
    """

    def __init__(self):
        self.running = False
        self.paused = False
        self.interval = 3600
        self.max_cycles = 1
        self.cycles_executed = 0
        self.last_run = None
        self.last_result = None
        self._task = None

    async def run_once(self):
        """
        Executa exatamente um ciclo autônomo.
        """
        result = await (
            autonomous_cycle_orchestrator
            .run_cycle()
        )

        self.cycles_executed += 1
        self.last_run = datetime.utcnow().isoformat()
        self.last_result = result

        return result

    async def _loop(self):
        while self.running:

            if not self.paused:

                if (
                    self.max_cycles > 0
                    and self.cycles_executed >= self.max_cycles
                ):
                    self.running = False
                    break

                await self.run_once()

            await asyncio.sleep(
                max(10, self.interval)
            )

    def start(
        self,
        interval=3600,
        max_cycles=1
    ):
        if self.running:
            return {
                "status": "already_running"
            }

        self.interval = max(
            10,
            int(interval)
        )

        self.max_cycles = max(
            1,
            int(max_cycles)
        )

        self.cycles_executed = 0
        self.running = True
        self.paused = False

        self._task = asyncio.create_task(
            self._loop()
        )

        return {
            "status": "started",
            "interval_seconds": self.interval,
            "max_cycles": self.max_cycles,
            "financial_policy": {
                "automatic_revenue_threshold_brl": 1000.0,
                "automatic_spend_limit_brl": 100.0,
                "owner_controls_capital": True,
            }
        }

    def pause(self):
        self.paused = True

        return {
            "status": "paused"
        }

    def resume(self):
        self.paused = False

        return {
            "status": "resumed"
        }

    def stop(self):
        self.running = False
        self.paused = False

        if self._task:
            self._task.cancel()
            self._task = None

        return {
            "status": "stopped"
        }

    def status(self):
        return {
            "running": self.running,
            "paused": self.paused,
            "interval_seconds": self.interval,
            "max_cycles": self.max_cycles,
            "cycles_executed": self.cycles_executed,
            "last_run": self.last_run,
            "last_result": self.last_result,
            "financial_policy": {
                "automatic_revenue_threshold_brl": 1000.0,
                "automatic_spend_limit_brl": 100.0,
                "owner_controls_capital": True,
            }
        }


autonomous_scheduler_bridge = (
    AutonomousSchedulerBridge()
)
