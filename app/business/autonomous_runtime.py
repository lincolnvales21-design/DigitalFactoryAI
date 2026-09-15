import asyncio
import logging
import os
from datetime import datetime, timezone

from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator,
)
from app.business.emergency_shutdown import (
    emergency_shutdown,
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

        self.interval_seconds = max(
            10,
            int(
                os.getenv(
                    "DIGITALFACTORY_AUTONOMOUS_INTERVAL",
                    "900",
                )
            ),
        )

        self._task = None
        self._running = False
        self._cycle_lock = asyncio.Lock()

        # STOP explícito do proprietário.
        # O middleware não pode religar automaticamente.
        self.owner_stopped = False

        self.started_at = None
        self.stopped_at = None
        self.last_cycle = None
        self.last_result = None
        self.last_error = None
        self.current_objective = None

        self.cycles_completed = 0
        self.cycles_failed = 0

    # ========================================================
    # KILL SWITCH
    # ========================================================

    def _emergency_off(self):
        try:
            return emergency_shutdown.is_emergency_off()
        except Exception:
            # Falha ao consultar o mecanismo de segurança
            # deve bloquear a autonomia.
            return True

    # ========================================================
    # EXECUÇÃO DE UM CICLO
    # ========================================================

    async def run_once(self):

        if self._emergency_off():
            self.last_result = {
                "status": "emergency_off",
                "executed": False,
                "reason": "Kill Switch ativo.",
            }
            return self.last_result

        if self._cycle_lock.locked():
            return {
                "status": "busy",
                "executed": False,
            }

        async with self._cycle_lock:

            if self._emergency_off():
                self.last_result = {
                    "status": "emergency_off",
                    "executed": False,
                    "reason": "Kill Switch ativo.",
                }
                return self.last_result

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

                self.last_result = result

                if isinstance(result, dict):
                    decision = result.get("decision")

                    if isinstance(decision, dict):
                        self.current_objective = (
                            decision.get("reason")
                            or decision.get("objective")
                        )

                    if not self.current_objective:
                        self.current_objective = (
                            result.get("objective")
                        )

                status = (
                    result.get("status")
                    if isinstance(result, dict)
                    else None
                )

                if status in {
                    "failed",
                    "error",
                }:
                    self.cycles_failed += 1

                elif status not in {
                    "busy",
                    "emergency_off",
                }:
                    self.cycles_completed += 1

                logger.warning(
                    "DIGITALFACTORY AUTONOMOUS CYCLE FINISHED: %s",
                    status,
                )

                return result

            except Exception as exc:

                self.cycles_failed += 1
                self.last_error = str(exc)

                self.last_result = {
                    "status": "failed",
                    "executed": False,
                    "reason": str(exc),
                }

                logger.exception(
                    "ERRO NO CICLO AUTONOMO"
                )

                return self.last_result

    # ========================================================
    # LOOP CONTÍNUO
    # ========================================================

    async def _loop(self):

        self._running = True

        logger.warning(
            "DIGITALFACTORY AUTONOMOUS RUNTIME ONLINE"
        )

        while self._running:

            # Kill Switch possui prioridade absoluta.
            if self._emergency_off():
                self._running = False

                self.last_result = {
                    "status": "emergency_off",
                    "executed": False,
                    "reason": (
                        "Kill Switch ativado pelo proprietário."
                    ),
                }

                break

            try:
                await self.run_once()

            except asyncio.CancelledError:
                break

            except Exception as exc:
                self.last_error = str(exc)
                self.cycles_failed += 1

                logger.exception(
                    "ERRO PROTEGIDO NO RUNTIME"
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

    # ========================================================
    # START
    # ========================================================

    def start(self, owner_action=False):

        if owner_action:
            self.owner_stopped = False

        if self.owner_stopped and not owner_action:
            return {
                "status": "owner_stopped",
                "started": False,
                "reason": (
                    "Runtime parado explicitamente pelo proprietário."
                ),
            }

        if not self.enabled:
            logger.warning(
                "DIGITALFACTORY AUTONOMOUS RUNTIME DISABLED"
            )

            return {
                "status": "disabled",
                "started": False,
            }

        if self._emergency_off():
            logger.warning(
                "AUTONOMOUS RUNTIME BLOCKED BY EMERGENCY KILL SWITCH"
            )

            return {
                "status": "emergency_off",
                "started": False,
            }

        if (
            self._task is not None
            and not self._task.done()
        ):
            return {
                "status": "already_running",
                "started": False,
            }

        self._running = True

        self.started_at = (
            datetime.now(timezone.utc).isoformat()
        )

        self.stopped_at = None

        self._task = asyncio.create_task(
            self._loop(),
            name="digitalfactory-autonomous-runtime",
        )

        logger.warning(
            "DIGITALFACTORY AUTONOMOUS RUNTIME TASK CREATED"
        )

        return {
            "status": "started",
            "started": True,
            "started_at": self.started_at,
            "interval_seconds": self.interval_seconds,
        }

    # ========================================================
    # STOP
    # ========================================================

    async def stop(self, owner_action=False):

        if owner_action:
            self.owner_stopped = True

        self._running = False

        task = self._task
        self._task = None

        self.stopped_at = (
            datetime.now(timezone.utc).isoformat()
        )

        if task is not None:

            task.cancel()

            try:
                await task

            except asyncio.CancelledError:
                pass

            except Exception:
                logger.exception(
                    "Erro ao encerrar runtime autônomo."
                )

        return {
            "status": "stopped",
            "stopped_at": self.stopped_at,
        }

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        task_active = (
            self._task is not None
            and not self._task.done()
        )

        return {
            "enabled": self.enabled,
            "running": self._running,
            "task_active": task_active,
            "owner_stopped": self.owner_stopped,
            "emergency_off": self._emergency_off(),
            "interval_seconds": self.interval_seconds,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "last_cycle": self.last_cycle,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "current_objective": self.current_objective,
            "cycles_completed": self.cycles_completed,
            "cycles_failed": self.cycles_failed,
            "autonomous": True,
            "dashboard_required": False,
            "financial_policy": {
                "automatic_revenue_threshold_brl": 1000.0,
                "automatic_spend_limit_brl": 100.0,
                "automatic_spending_below_threshold": False,
                "owner_controls_capital": True,
            },
        }


autonomous_runtime = AutonomousRuntime()
