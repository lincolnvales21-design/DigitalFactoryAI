import traceback
import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.business.opportunity_engine import opportunity_engine
from app.business.novelty_engine import novelty_engine
from app.business.offer_engine import offer_engine
from app.business.sales_engine import sales_engine
from app.business.social_publisher import social_publisher
from app.business.organic_distribution_engine import organic_distribution_engine
from app.business.learning_engine import learning_engine
from app.business.emergency_shutdown import emergency_shutdown
from app.business.engine import business_engine
from app.products.factory import product_factory

from app.business.autonomous_decision_loop import autonomous_decision_loop
from app.agents.loader import load_agents


class AutonomousBusinessEngine:

    def __init__(self):
        self._lock = asyncio.Lock()
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _ensure_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                objective TEXT,
                opportunity_json TEXT,
                result_json TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _save_cycle(
        self,
        started_at,
        status,
        objective=None,
        opportunity=None,
        result=None,
        completed_at=None,
    ):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO autonomous_cycles
            (
                started_at,
                completed_at,
                status,
                objective,
                opportunity_json,
                result_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                started_at,
                completed_at,
                status,
                objective,
                json.dumps(opportunity, ensure_ascii=False)
                if opportunity is not None else None,
                json.dumps(result, ensure_ascii=False)
                if result is not None else None,
            ),
        )

        cycle_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return cycle_id

    async def run_once(self):

        # ========================================================
        # KILL SWITCH — BARREIRA 1
        # ========================================================

        if emergency_shutdown.is_emergency_off():
            return {
                "status": "emergency_off",
                "executed": False,
                "message": (
                    "Business Engine bloqueado pelo "
                    "Kill Switch antes da produção."
                ),
            }

        # Garante que todos os agentes estejam disponíveis
        # antes de iniciar qualquer ciclo comercial.
        load_agents()

        # ========================================================
        # KILL SWITCH — BARREIRA 2
        # ========================================================

        if emergency_shutdown.is_emergency_off():
            return {
                "status": "emergency_off",
                "executed": False,
                "message": (
                    "Produção interrompida pelo "
                    "Kill Switch após carregamento dos agentes."
                ),
            }

        if self._lock.locked():
            return {
                "status": "busy",
                "message": "Um ciclo autônomo já está em execução.",
            }

        async with self._lock:

            started_at = datetime.utcnow().isoformat()

            cycle_id = self._save_cycle(
                started_at=started_at,
                status="running",
            )

            try:

                # ------------------------------------------------
                # 1. DESCOBRIR OPORTUNIDADE
                # ------------------------------------------------

                if emergency_shutdown.is_emergency_off():
                    return {
                        "status": "emergency_off",
                        "executed": False,
                        "message": (
                            "Descoberta de oportunidade bloqueada "
                            "pelo Kill Switch."
                        ),
                    }

                opportunity_result = await opportunity_engine.select()

                opportunity = opportunity_result["selected"]

                # ------------------------------------------------
                # 2. ANALISAR NOVIDADE E DIFERENCIAÇÃO
                # ------------------------------------------------

                novelty_result = await novelty_engine.evaluate(
                    opportunity
                )

                # ------------------------------------------------
                # QUALITY GATE DE NOVIDADE
                # ------------------------------------------------

                if novelty_result.get("decision") != "ready_for_product_creation":

                    result = {
                        "status": "rejected",
                        "stage": "novelty",
                        "message": (
                            "Oportunidade rejeitada pelo "
                            "quality gate de novidade."
                        ),
                        "opportunity": opportunity,
                        "novelty": novelty_result,
                    }

                    completed_at = datetime.utcnow().isoformat()

                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        UPDATE autonomous_cycles
                        SET
                            completed_at = ?,
                            status = ?,
                            objective = ?,
                            opportunity_json = ?,
                            result_json = ?
                        WHERE id = ?
                        """,
                        (
                            completed_at,
                            "rejected",
                            None,
                            json.dumps(
                                opportunity,
                                ensure_ascii=False,
                            ),
                            json.dumps(
                                result,
                                ensure_ascii=False,
                            ),
                            cycle_id,
                        ),
                    )

                    conn.commit()
                    conn.close()

                    return {
                        "status": "rejected",
                        "cycle_id": cycle_id,
                        "opportunity": opportunity,
                        "novelty": novelty_result,
                    }

                # ------------------------------------------------
                # 3. TRANSFORMAR OPORTUNIDADE EM OBJETIVO
                # ------------------------------------------------

                area = opportunity.get(
                    "area",
                    "mercado digital",
                )

                problem = opportunity.get(
                    "problem",
                    "resolver um problema específico",
                )

                audience = opportunity.get(
                    "target_audience",
                    "público interessado na solução",
                )

                fmt = opportunity.get(
                    "recommended_format",
                    "produto digital",
                )

                angle = novelty_result.get(
                    "product_angle",
                    "",
                )

                differentiation = novelty_result.get(
                    "differentiation_strategy",
                    "",
                )

                mechanism = novelty_result.get(
                    "unique_mechanism",
                    "",
                )

                commercial_thesis = novelty_result.get(
                    "commercial_thesis",
                    "",
                )

                objective = (
                    f"Área: {area}. "
                    f"Problema: {problem}. "
                    f"Público: {audience}. "
                    f"Formato recomendado: {fmt}. "
                    f"Mercado: {opportunity.get('market', '')}. "
                    f"Decisão comercial: "
                    f"{novelty_result.get('decision', '')}. "
                    f"Ângulo do produto: {angle}. "
                    f"Diferenciação: {differentiation}. "
                    f"Mecanismo: {mechanism}. "
                    f"Tese comercial: {commercial_thesis}."
                )

                # ------------------------------------------------
                # 4. EXECUTAR ENGINE EXISTENTE
                # ------------------------------------------------

                result = await business_engine.run(objective)

                # ------------------------------------------------
                # 5. CRIAR OFERTA COMERCIAL
                # ------------------------------------------------

                product_result = None

                if isinstance(result, dict):

                    for item in result.get(
                        "results",
                        [],
                    ):

                        if item.get("stage") == "product":

                            product_result = item.get(
                                "result"
                            )

                            break

                product_data = (
                    product_result
                    if isinstance(
                        product_result,
                        dict,
                    )
                    else {}
                )

                # ------------------------------------------------
                                # OFERTA OFICIAL DO CICLO
                #
                # O MarketingAgent e a unica fonte oficial da oferta.
                # O resultado pode estar aninhado em:
                #
                # result
                #   -> results
                #      -> marketing
                #         -> result
                #            -> execution
                #               -> offer
                #
                # Fazemos uma busca recursiva somente dentro
                # do resultado do MarketingAgent.

                def find_offer(value):

                    if isinstance(value, dict):

                        direct_offer = value.get("offer")

                        if isinstance(
                            direct_offer,
                            dict,
                        ):
                            return direct_offer

                        for nested_value in value.values():

                            found = find_offer(
                                nested_value
                            )

                            if isinstance(
                                found,
                                dict,
                            ):
                                return found

                    elif isinstance(value, list):

                        for nested_value in value:

                            found = find_offer(
                                nested_value
                            )

                            if isinstance(
                                found,
                                dict,
                            ):
                                return found

                    return None


                offer_result = None

                if isinstance(
                    result,
                    dict,
                ):

                    for item in result.get(
                        "results",
                        [],
                    ):

                        if not isinstance(
                            item,
                            dict,
                        ):
                            continue

                        if item.get("stage") != "marketing":
                            continue

                        marketing_result = item.get(
                            "result"
                        )

                        if isinstance(
                            marketing_result,
                            dict,
                        ):

                            offer_result = find_offer(
                                marketing_result
                            )

                        break


                # O MarketingAgent e a unica fonte oficial da oferta.
                # Se nao houver oferta valida, o ciclo registra bloqueio.
                if not isinstance(
                    offer_result,
                    dict,
                ):

                    offer_result = {
                        "status": "blocked",
                        "reason": (
                            "MarketingAgent nao forneceu "
                            "uma oferta comercial valida."
                        ),
                    }

                if isinstance(
                    result,
                    dict,
                ):

                    result["offer"] = offer_result

# 6. PUBLICAÇÃO COM QUALITY GATE
                # ------------------------------------------------

                product_id = None

                if isinstance(
                    product_result,
                    dict,
                ):

                    product_id = (
                        product_result.get(
                            "product_id"
                        )
                        or product_result.get(
                            "id"
                        )
                    )

                publication_result = None

                if product_id:

                    # =================================================
                    # BARREIRA: FACTORY → PUBLICAÇÃO
                    # =================================================

                    factory_status = product_data.get(
                        "factory_status"
                    )

                    factory_result = product_data.get(
                        "factory",
                        {},
                    )

                    factory_approved = (
                        factory_status == "success"
                        and factory_result.get(
                            "quality_gate",
                            {},
                        ).get("status") == "approved"
                    )

                    if not factory_approved:

                        publication_result = {
                            "status": "blocked",
                            "product_id": int(product_id),
                            "reason": (
                                "Publicação bloqueada: "
                                "ProductFactory não aprovou "
                                "a produção."
                            ),
                            "factory_status": factory_status,
                        }

                    else:

                        # ====================================================
                        # KILL SWITCH — BARREIRA 3
                        # ====================================================

                        if emergency_shutdown.is_emergency_off():
                            publication_result = {
                                "status": "emergency_off",
                                "product_id": int(product_id),
                                "reason": (
                                    "Publicação comercial bloqueada "
                                    "pelo Kill Switch."
                                ),
                            }

                        else:

                            publication_result = sales_engine.publish(
                                product_id=int(product_id),
                                offer=offer_result,
                            )

                        # ------------------------------------------------
                        # PUBLICAÇÃO ORGÂNICA AUTOMÁTICA
                        # ------------------------------------------------
                        # Só publica no Instagram depois que o produto
                        # passou pelo ProductFactory + SalesEngine.
                        # Publicação orgânica possui custo financeiro R$0.

                        if (
                            isinstance(publication_result, dict)
                            and publication_result.get("status") == "published"
                        ):
                            social_product = {
                                "id": int(product_id),
                                "name": (
                                    offer_result.get("offer_name")
                                    or "Produto Digital"
                                ),
                            }

                            # ------------------------------------------------
                            # DISTRIBUIÇÃO ORGÂNICA INTELIGENTE
                            # ------------------------------------------------
                            # Escolhe automaticamente a próxima variação
                            # ainda não publicada para este produto.

                            organic_variation = (
                                organic_distribution_engine.next_variation(
                                    product_id=int(product_id),
                                    offer=offer_result,
                                    product=social_product,
                                )
                            )

                            if organic_variation:

                                # =================================================
                                # KILL SWITCH — BARREIRA 4
                                # =================================================

                                if emergency_shutdown.is_emergency_off():
                                    social_result = {
                                        "status": "emergency_off",
                                        "published": False,
                                        "reason": (
                                            "Publicação social bloqueada "
                                            "pelo Kill Switch."
                                        ),
                                    }

                                else:

                                    social_result = (
                                        await social_publisher.publish(
                                        product=social_product,
                                        offer=offer_result,
                                        variation=organic_variation,
                                        )
                                    )

                                publication_result["social"] = social_result
                                publication_result["organic_variation"] = {
                                    "content_type": organic_variation.get(
                                        "content_type"
                                    ),
                                    "title": organic_variation.get(
                                        "title"
                                    ),
                                    "medium": organic_variation.get(
                                        "medium"
                                    ),
                                    "tracking_url": organic_variation.get(
                                        "tracking_url"
                                    ),
                                }

                            else:

                                publication_result["social"] = {
                                    "status": "skipped",
                                    "product_id": int(product_id),
                                    "reason": (
                                        "Todas as variações orgânicas "
                                        "disponíveis para este produto "
                                        "já foram publicadas."
                                    ),
                                }

                if isinstance(result, dict):

                    result["publication"] = publication_result

                # ------------------------------------------------
                # 7. APRENDIZADO
                # ------------------------------------------------

                learning_result = learning_engine.learn()

                if isinstance(result, dict):

                    result["learning"] = learning_result

                # ------------------------------------------------
                # 8. FINALIZAR CICLO
                # ------------------------------------------------

                completed_at = datetime.utcnow().isoformat()

                if isinstance(result, dict):

                    status = (
                        "completed"
                        if result.get("status") == "success"
                        else "failed"
                    )

                else:

                    status = "failed"

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE autonomous_cycles
                    SET
                        completed_at = ?,
                        status = ?,
                        objective = ?,
                        opportunity_json = ?,
                        result_json = ?
                    WHERE id = ?
                    """,
                    (
                        completed_at,
                        status,
                        objective,
                        json.dumps(
                            opportunity,
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            result,
                            ensure_ascii=False,
                        ),
                        cycle_id,
                    ),
                )

                conn.commit()
                conn.close()

                return {
                    "status": status,
                    "cycle_id": cycle_id,
                    "objective": objective,
                    "opportunity": opportunity,
                    "result": result,
                }

            except Exception as exc:

                traceback.print_exc()
                completed_at = datetime.utcnow().isoformat()

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE autonomous_cycles
                    SET
                        completed_at = ?,
                        status = ?,
                        result_json = ?
                    WHERE id = ?
                    """,
                    (
                        completed_at,
                        "failed",
                        json.dumps(
                            {
                                "error": str(exc),
                            },
                            ensure_ascii=False,
                        ),
                        cycle_id,
                    ),
                )

                conn.commit()
                conn.close()

                return {
                    "status": "failed",
                    "cycle_id": cycle_id,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }

    def status(self):

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                started_at,
                completed_at,
                status,
                objective
            FROM autonomous_cycles
            ORDER BY id DESC
            LIMIT 10
        """)

        rows = cursor.fetchall()

        conn.close()

        return {
            "running": self._lock.locked(),
            "cycles": [
                {
                    "id": row[0],
                    "started_at": row[1],
                    "completed_at": row[2],
                    "status": row[3],
                    "objective": row[4],
                }
                for row in rows
            ],
        }


autonomous_business_engine = AutonomousBusinessEngine()
