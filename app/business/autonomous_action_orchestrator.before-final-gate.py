import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.agents.manager import manager
from app.security.permissions import Role

from app.business.action_execution_engine import (
    action_execution_engine
)

from app.business.autonomous_decision_loop import (
    autonomous_decision_loop
)

from app.business.emergency_shutdown import (
    emergency_shutdown
)


class AutonomousActionOrchestrator:

    AGENT_MAP = {
        "expand_winner": "ProductAgent",
        "expand_product": "ProductAgent",
        "create_variation": "ProductAgent",
        "create_product_variation": "ProductAgent",
        "optimize_conversion": "MarketingAgent",
        "optimize_offer": "MarketingAgent",
        "validate_before_expansion": "ResearchAgent",
        "validate_product": "ResearchAgent",
        "discover_new_opportunity": "ResearchAgent",
        "discover_opportunity": "ResearchAgent",
    }

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_action_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                agent TEXT,
                product_id INTEGER,
                status TEXT NOT NULL,
                objective TEXT,
                result_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def get_decision(self):
        return autonomous_decision_loop.build_cycle_objective()

    def select_agent(self, action):
        return self.AGENT_MAP.get(
            action,
            "ResearchAgent"
        )

    def build_agent_objective(self, decision):

        action = decision.get("optimization_action")
        product_id = decision.get("product_id")
        product = decision.get("product")

        if action in (
            "expand_winner",
            "expand_product",
        ):
            return (
                f"Expandir o produto vencedor "
                f"#{product_id} ({product}). "
                "Pesquisar novas extensões, "
                "variações, complementos e "
                "novos produtos derivados "
                "com potencial comercial. "
                "Priorizar oportunidades com "
                "evidência de demanda."
            )

        if action in (
            "create_variation",
            "create_product_variation",
        ):
            return (
                f"Criar uma nova variação do "
                f"produto #{product_id} ({product}), "
                "mantendo o problema central "
                "e explorando um novo ângulo "
                "comercial. "
                "A nova solução deve possuir "
                "diferenciação clara."
            )

        if action == "optimize_conversion":
            return (
                f"Otimizar a conversão do "
                f"produto #{product_id} ({product}). "
                "Identificar obstáculos à compra, "
                "melhorar comunicação, "
                "posicionamento, chamada para ação "
                "e clareza da oferta. "
                "Não inventar depoimentos ou resultados."
            )

        if action == "optimize_offer":
            return (
                f"Otimizar a oferta do "
                f"produto #{product_id} ({product}). "
                "Melhorar posicionamento, "
                "promessa, benefícios, "
                "tratamento de objeções, "
                "copy e chamada para ação."
            )

        if action in (
            "validate_before_expansion",
            "validate_product",
        ):
            return (
                f"Validar comercialmente o "
                f"produto #{product_id} ({product}). "
                "Pesquisar evidências de demanda, "
                "identificar sinais positivos e "
                "negativos e determinar quais "
                "ajustes devem ser realizados "
                "antes de uma expansão."
            )

        return (
            "Descobrir uma nova oportunidade "
            "comercial com potencial para "
            "um produto digital diferenciado. "
            "Investigar problema, público, "
            "demanda, diferenciação e "
            "potencial comercial antes da produção."
        )

    async def execute_decision(self):

        # ====================================================
        # KILL SWITCH
        # ====================================================

        if emergency_shutdown.is_emergency_off():

            result = {
                "status": "emergency_off",
                "executed": False,
                "message": (
                    "Ação bloqueada pelo "
                    "desligamento de segurança máxima."
                ),
            }

            self._log(
                action="blocked",
                agent=None,
                product_id=None,
                status="emergency_off",
                objective=None,
                result=result,
            )

            return result

        # ====================================================
        # OBTER DECISÃO
        # ====================================================

        plan = self.get_decision()

        if not isinstance(plan, dict):

            return {
                "status": "failed",
                "executed": False,
                "error": (
                    "Decision Loop não retornou "
                    "uma decisão válida."
                ),
            }

        decision = plan.get(
            "decision",
            {}
        )

        if not isinstance(decision, dict):
            decision = {}

        # ====================================================
        # BARREIRA DE DECISÃO
        # ====================================================

        gate_decision = decision.get(
            "gate_decision"
        )

        cycle_action = decision.get(
            "cycle_action"
        )

        should_run = decision.get(
            "should_run"
        )

        decision_reason = decision.get(
            "reason",
            "Decisão determinou aguardar."
        )

        if (
            gate_decision in {"wait", "WAIT"}
            or cycle_action in {"wait", "WAIT"}
            or should_run is False
        ):

            result = {
                "status": "waiting",
                "executed": False,
                "action": "wait",
                "product_id": decision.get(
                    "product_id"
                ),
                "reason": decision_reason,
                "decision": decision,
                "capital_policy": decision.get(
                    "capital_policy"
                ),
            }

            self._log(
                action="wait",
                agent=None,
                product_id=decision.get(
                    "product_id"
                ),
                status="waiting",
                objective=decision.get(
                    "objective"
                ),
                result=result,
            )

            return result

        # ====================================================
        # AÇÃO
        # ====================================================

        action = decision.get(
            "optimization_action"
        )

        if not action:
            action = decision.get(
                "action"
            )

        if not action:
            action = "discover_opportunity"

        product_id = decision.get(
            "product_id"
        )

        # ====================================================
        # AGENTE
        # ====================================================

        agent_name = self.select_agent(
            action
        )

        # ====================================================
        # OBJETIVO
        # ====================================================

        objective = self.build_agent_objective(
            decision
        )

        # ====================================================
        # CONTROLE FINANCEIRO
        # ====================================================

        execution_gate = (
            await action_execution_engine.execute(
                action=action,
                product_id=product_id,
                estimated_cost=0.0,
            )
        )

        if not isinstance(
            execution_gate,
            dict
        ):

            result = {
                "status": "blocked",
                "executed": False,
                "action": action,
                "product_id": product_id,
                "reason": (
                    "Controle financeiro "
                    "não retornou autorização válida."
                ),
            }

            self._log(
                action=action,
                agent=agent_name,
                product_id=product_id,
                status="blocked",
                objective=objective,
                result=result,
            )

            return result

        if execution_gate.get(
            "status"
        ) != "executed":

            result = {
                "status": "blocked",
                "executed": False,
                "action": action,
                "agent": agent_name,
                "product_id": product_id,
                "objective": objective,
                "reason": (
                    "Ação bloqueada pelo "
                    "controle financeiro."
                ),
                "capital_policy": (
                    execution_gate.get(
                        "capital_policy"
                    )
                ),
            }

            self._log(
                action=action,
                agent=agent_name,
                product_id=product_id,
                status="blocked",
                objective=objective,
                result=result,
            )

            return result

        # ====================================================
        # KILL SWITCH — ÚLTIMA BARREIRA
        # ====================================================

        if emergency_shutdown.is_emergency_off():

            result = {
                "status": "emergency_off",
                "executed": False,
                "action": action,
                "agent": agent_name,
                "message": (
                    "Execução bloqueada pelo "
                    "Kill Switch antes da entrega "
                    "ao agente."
                ),
            }

            self._log(
                action=action,
                agent=agent_name,
                product_id=product_id,
                status="blocked",
                objective=objective,
                result=result,
            )

            return result

        # ====================================================
        # EXECUTAR AGENTE
        # ====================================================

        try:

            agent_result = await manager.execute(
                Role.OWNER,
                "execute_agents",
                agent_name,
                objective,
            )

            # =================================================
            # FALHA DO AGENTE
            # =================================================

            if (
                isinstance(agent_result, dict)
                and agent_result.get("status")
                in {
                    "error",
                    "failed",
                    "blocked",
                }
            ):

                result = {
                    "status": "failed",
                    "executed": False,
                    "action": action,
                    "agent": agent_name,
                    "product_id": product_id,
                    "objective": objective,
                    "agent_result": agent_result,
                    "capital_policy": (
                        execution_gate.get(
                            "capital_policy"
                        )
                    ),
                    "decision": decision,
                }

                self._log(
                    action=action,
                    agent=agent_name,
                    product_id=product_id,
                    status="failed",
                    objective=objective,
                    result=result,
                )

                return result

            # =================================================
            # SUCESSO
            # =================================================

            result = {
                "status": "executed",
                "executed": True,
                "action": action,
                "agent": agent_name,
                "product_id": product_id,
                "objective": objective,
                "agent_result": agent_result,
                "capital_policy": (
                    execution_gate.get(
                        "capital_policy"
                    )
                ),
                "decision": decision,
            }

            self._log(
                action=action,
                agent=agent_name,
                product_id=product_id,
                status="executed",
                objective=objective,
                result=result,
            )

            return result

        except Exception as exc:

            result = {
                "status": "failed",
                "executed": False,
                "action": action,
                "agent": agent_name,
                "product_id": product_id,
                "objective": objective,
                "error": str(exc),
                "decision": decision,
            }

            self._log(
                action=action,
                agent=agent_name,
                product_id=product_id,
                status="failed",
                objective=objective,
                result=result,
            )

            return result

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    def _log(
        self,
        action,
        agent,
        product_id,
        status,
        objective,
        result,
    ):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO autonomous_action_runs
            (
                action,
                agent,
                product_id,
                status,
                objective,
                result_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action,
                agent,
                product_id,
                status,
                objective,
                json.dumps(
                    result,
                    ensure_ascii=False,
                    default=str,
                ),
                datetime.now(
                    timezone.utc
                ).isoformat(),
            ),
        )

        conn.commit()
        conn.close()


autonomous_action_orchestrator = (
    AutonomousActionOrchestrator()
)
