import asyncio
import logging
import os
from datetime import datetime, timezone

from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator,
)

logger = logging.getLogger("digitalfactory.autonomous_runtime")


class AutonomousRuntime:
    """
    Motor contínuo do DigitalFactoryAI.

    Responsabilidade:
    - executar ciclos autonomamente;
    - aguardar entre ciclos;
    - impedir dois ciclos simultâneos;
    - sobreviver a erros de um ciclo;
    - manter o processo ativo enquanto a aplicação estiver online.

    O motor não controla capital diretamente.
    As decisões financeiras continuam obedecendo
    às regras existentes do DigitalFactoryAI.
    """

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

    async def run_once(self):
        """
        Executa exatamente um ciclo completo.
        """
        if self._cycle_lock.locked():
            logger.info(
                "Ciclo ignorado: outro ciclo ainda está executando."
            )
            return {
                "status": "busy",
                "executed": False,
            }

        async with self._cycle_lock:
            started_at = datetime.now(
                timezone.utc
            ).isoformat()

            logger.info(
                "AUTONOMOUS CYCLE STARTED: %s",
                started_at,
            )

            try:
                result = await (
                    autonomous_cycle_orchestrator.run_cycle()
                )

                logger.info(
                    "AUTONOMOUS CYCLE FINISHED: %s",
                    result.get("status")
                    if isinstance(result, dict)
                    else "completed",
                )

                return result

            except Exception as exc:
                logger.exception(
                    "Erro no ciclo autônomo: %s",
                    exc,
                )

                return {
                    "status": "failed",
                    "executed": False,
                    "reason": str(exc),
                }

    async def _loop(self):
        """
        Loop principal 24/7.
        """
        if not self.enabled:
            logger.warning(
                "Autonomia contínua desativada por configuração."
            )
            return

        self._running = True

        logger.info(
            "DIGITALFACTORY AUTONOMOUS RUNTIME ONLINE"
        )

        while self._running:

            await self.run_once()

            if not self._running:
                break

            logger.info(
                "Próximo ciclo autônomo em %s segundos.",
                self.interval_seconds,
            )

            try:
                await asyncio.sleep(
                    self.interval_seconds
                )
            except asyncio.CancelledError:
                logger.info(
                    "Autonomous Runtime interrompido."
                )
                break

        self._running = False

        logger.info(
            "DIGITALFACTORY AUTONOMOUS RUNTIME OFFLINE"
        )

    def start(self):
        """
        Inicia o loop em background.
        """
        if self._task is not None:
            if not self._task.done():
                return

        self._task = asyncio.create_task(
            self._loop(),
            name="digitalfactory-autonomous-runtime",
        )

        logger.info(
            "Autonomous Runtime task criada."
        )

    async def stop(self):
        """
        Para o loop de forma segura.
        """
        self._running = False

        if self._task is not None:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._task = None

        logger.info(
            "Autonomous Runtime parado."
        )

    def status(self):
        return {
            "enabled": self.enabled,
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "task_active": (
                self._task is not None
                and not self._task.done()
            ),
        }


autonomous_runtime = AutonomousRuntime()
