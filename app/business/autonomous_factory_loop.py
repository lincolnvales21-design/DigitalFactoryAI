import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv

from app.business.autonomous_cycle_gate import (
    autonomous_cycle_gate
)
from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator
)
from app.business.emergency_shutdown import emergency_shutdown


load_dotenv()


class AutonomousFactoryLoop:
    """
    Loop principal da fábrica autônoma.

    INICIAR:
        inicia a execução contínua.

    PAUSAR:
        interrompe temporariamente a execução,
        preservando o estado da fábrica.

    RETOMAR:
        continua a execução após uma pausa.

    PARAR:
        encerra a execução normal,
        sem apagar a memória de evolução.

    DESLIGAR:
        Kill Switch de emergência.
        Bloqueia a autonomia e é tratado
        pela camada de emergência.

    A política financeira continua centralizada
    no ActionExecutionEngine.
    """

    def __init__(self):
        self.running = False
        self.paused = False
        self.interval = 3600
        self.cycles = 0
        self.started_at = None
        self.stopped_at = None
        self.last_result = None
        self.last_gate = None
        self._task = None
        self._lock = asyncio.Lock()

    async def _loop(self):

        while self.running:

            # ------------------------------------------------
            # KILL SWITCH — PRIORIDADE MÁXIMA
            # ------------------------------------------------

            if emergency_shutdown.is_emergency_off():

                self.running = False
                self.paused = False
                self.stopped_at = (
                    datetime.now(timezone.utc).isoformat()
                )

                self.last_result = {
                    "status": "emergency_off",
                    "reason": (
                        "Kill Switch ativado pelo proprietário"
                    ),
                }

                self._task = None

                return

            # ------------------------------------------------
            # PAUSA
            # ------------------------------------------------

            if not self.paused:

                try:

                    # ----------------------------------------
                    # CYCLE GATE
                    # ----------------------------------------

                    gate = autonomous_cycle_gate.analyze()

                    self.last_gate = gate

                    # ----------------------------------------
                    # WAIT
                    # ----------------------------------------

                    if not gate.get(
                        "should_run",
                        False
                    ):

                        self.last_result = {
                            "status": "waiting",
                            "reason": gate.get(
                                "reason"
                            ),
                            "gate": gate,
                        }

                    # ----------------------------------------
                    # EXECUTAR CICLO
                    # ----------------------------------------

                    else:

                        result = await (
                            autonomous_cycle_orchestrator
                            .run_cycle()
                        )

                        self.cycles += 1

                        self.last_result = result

                except asyncio.CancelledError:

                    # PARAR normal cancela a tarefa
                    # deliberadamente. Não é erro.
                    self.last_result = {
                        "status": "stopped",
                        "reason": (
                            "Execução interrompida pelo "
                            "controle da fábrica."
                        ),
                    }

                    raise

                except Exception as exc:

                    self.last_result = {
                        "status": "error",
                        "error": str(exc),
                    }

            # ------------------------------------------------
            # INTERVALO
            # ------------------------------------------------

            try:

                await asyncio.sleep(
                    max(10, self.interval)
                )

            except asyncio.CancelledError:

                raise

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    async def start(self, interval=3600):

        async with self._lock:

            # --------------------------------------------
            # KILL SWITCH BLOQUEIA NOVO START
            # --------------------------------------------

            if emergency_shutdown.is_emergency_off():

                return {
                    "status": "emergency_off",
                    "started": False,
                    "message": (
                        "Fábrica bloqueada pelo "
                        "desligamento de segurança máxima."
                    ),
                }

            # --------------------------------------------
            # JÁ ESTÁ RODANDO
            # --------------------------------------------

            if self.running:

                return {
                    "status": "already_running",
                    "cycles": self.cycles,
                }

            # --------------------------------------------
            # CONFIGURAÇÃO
            # --------------------------------------------

            self.interval = max(
                10,
                int(interval)
            )

            self.running = True
            self.paused = False
            self.cycles = 0

            self.started_at = (
                datetime.now(timezone.utc)
                .isoformat()
            )

            self.stopped_at = None
            self.last_result = None
            self.last_gate = None

            # --------------------------------------------
            # INICIAR LOOP
            # --------------------------------------------

            self._task = asyncio.create_task(
                self._loop()
            )

            return {
                "status": "started",
                "interval_seconds": self.interval,
                "started_at": self.started_at,
            }

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    async def stop(self):

        async with self._lock:

            if not self.running:

                return {
                    "status": "already_stopped"
                }

            # --------------------------------------------
            # PARAR NORMAL
            # --------------------------------------------

            self.running = False
            self.paused = False

            task = self._task
            self._task = None

            self.stopped_at = (
                datetime.now(timezone.utc)
                .isoformat()
            )

            # --------------------------------------------
            # CANCELAR LOOP
            # --------------------------------------------

            if task:

                task.cancel()

            return {
                "status": "stopped",
                "stopped_at": self.stopped_at,
                "cycles_executed": self.cycles,
            }

    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    def pause(self):

        if not self.running:

            return {
                "status": "stopped"
            }

        self.paused = True

        return {
            "status": "paused"
        }

    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    def resume(self):

        if not self.running:

            return {
                "status": "stopped"
            }

        if emergency_shutdown.is_emergency_off():

            return {
                "status": "emergency_off",
                "resumed": False,
                "message": (
                    "Retomada bloqueada pelo "
                    "desligamento de segurança máxima."
                ),
            }

        self.paused = False

        return {
            "status": "resumed"
        }

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def status(self):

        return {
            "emergency_off": (
                emergency_shutdown.is_emergency_off()
            ),

            "running": self.running,

            "paused": self.paused,

            "interval_seconds": self.interval,

            "cycles_executed": self.cycles,

            "started_at": self.started_at,

            "stopped_at": self.stopped_at,

            "last_gate": self.last_gate,

            "last_result": self.last_result,

            "controls": {
                "start": True,
                "stop_requires_secret": True,
                "pause": True,
                "resume": True,
            },

            "financial_policy": {
                "automatic_revenue_threshold_brl": 1000.0,
                "automatic_spend_limit_brl": 100.0,
                "owner_controls_capital": True,
            },
        }


autonomous_factory_loop = AutonomousFactoryLoop()
