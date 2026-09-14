import re
from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge

from app.business.offer_engine import (
    offer_engine
)

from app.business.sales_engine import (
    sales_engine
)

from app.business.publication_tracker import (
    publication_tracker
)



class MarketingAgent(BaseAgent):

    def __init__(self):

        super().__init__("MarketingAgent")

        self.add_capability("marketing_strategy")
        self.add_capability("copywriting")
        self.add_capability("sales_page")
        self.add_capability("campaign_creation")

    async def execute_task(self, task: str):

        # =====================================================
        # 1. CONTEXTO DO PRODUTO
        # =====================================================

        # Se a tarefa informa explicitamente "produto #N",
        # esse produto tem prioridade sobre a memória mais recente.
        task_product_match = re.search(
            r"(?:produto|product)\s*#?\s*(\d+)",
            task,
            re.IGNORECASE,
        )

        requested_product_id = (
            int(task_product_match.group(1))
            if task_product_match
            else None
        )

        product = {}

        if requested_product_id is not None:

            try:
                import sqlite3

                conn = sqlite3.connect(
                    "digitalfactory.db"
                )
                conn.row_factory = sqlite3.Row

                row = conn.execute(
                    """
                    SELECT
                        id,
                        name,
                        description,
                        product_type,
                        price,
                        currency,
                        status,
                        created_at
                    FROM products
                    WHERE id = ?
                    """,
                    (requested_product_id,),
                ).fetchone()

                conn.close()

                if row:
                    product = dict(row)

            except Exception as exc:

                return {
                    "status": "error",
                    "agent": self.name,
                    "task": task,
                    "product_id": requested_product_id,
                    "message": (
                        "Erro ao carregar o produto "
                        f"#{requested_product_id}: {exc}"
                    ),
                }

            if not product:

                return {
                    "status": "error",
                    "agent": self.name,
                    "task": task,
                    "product_id": requested_product_id,
                    "message": (
                        "O produto informado na tarefa "
                        f"#{requested_product_id} não foi encontrado."
                    ),
                }

        else:

            product_context = memory.get_latest_result(
                "ProductAgent"
            )

            if not product_context:

                return {
                    "status": "error",
                    "agent": self.name,
                    "task": task,
                    "message": (
                        "Nenhum produto do ProductAgent "
                        "foi encontrado."
                    ),
                }

            if not requested_product_id:
                if isinstance(product_context, dict):

                    product = product_context.get(
                        "product",
                        {}
                    )

                    if not product:

                        execution = product_context.get(
                            "execution",
                            {}
                        )

                        product = execution.get(
                            "product",
                            {}
                        )

            if not isinstance(product, dict):

                product = {}

        knowledge_context = knowledge.latest()

        # =====================================================
        # 2. EXTRAIR PRODUTO
        # =====================================================

        product_id = product.get(
            "id"
        )

        if not product_id:

            return {
                "status": "error",
                "agent": self.name,
                "task": task,
                "message": (
                    "Produto encontrado, mas sem "
                    "product_id válido."
                ),
            }

        product_name = product.get(
            "name",
            "Produto Digital"
        )

        product_type = product.get(
            "type",
            product.get(
                "product_type",
                "digital_product"
            )
        )

        price = product.get(
            "price"
        )

        currency = product.get(
            "currency",
            "BRL"
        )

        # =====================================================
        # 3. PESQUISA DISPONÍVEL
        # =====================================================

        research_context = None
        research = {}

        # Produto explicitamente solicitado é soberano.
        # Não reutilizar pesquisa global de outro contexto/produto.
        if requested_product_id is None:
            research_context = memory.get_latest_result(
                "ResearchAgent"
            )

            if isinstance(research_context, dict):
                research = research_context.get(
                    "research",
                    research_context
                )

            if not isinstance(research, dict):
                research = {}

        # =====================================================
        # 4. NOVIDADE / DIFERENCIAÇÃO
        # =====================================================

        novelty = {}

        if requested_product_id is None and isinstance(
            product_context,
            dict
        ):

            product_definition = (
                product_context.get(
                    "product_definition",
                    {}
                )
            )

            if isinstance(
                product_definition,
                dict
            ):

                novelty = product_definition

        # =====================================================
        # 5. PREPARAR PRODUTO PARA O OFFER ENGINE
        # =====================================================

        # O ProductAgent já recebeu o Radar e consolidou
        # o contexto comercial. Ele é a fonte principal.
        if isinstance(
            novelty,
            dict,
        ):

            research = {
                **research,
                **{
                    key: value
                    for key, value in novelty.items()
                    if value not in (None, "")
                },
            }

        # =====================================================
        # CONTEXTO COMERCIAL CANÔNICO
        # =====================================================

        offer_product = {

            "id": product_id,

            "title": product_name,

            "name": product_name,

            "description": product.get(
                "description",
                ""
            ),

            "product_type": product_type,

            "price": price,

            "currency": currency,

            # Contexto específico vindo do Radar/ProductAgent
            "area": (
                novelty.get("area")
                or product.get("area")
                or research.get("area")
                or ""
            ),

            "problem": (
                novelty.get("problem")
                or product.get("problem")
                or (
                    "Profissionais autônomos perdem tempo com tarefas "
                    "administrativas repetitivas."
                    if any(
                        term in (
                            f"{product_name} "
                            f"{product.get('description', '')}"
                        ).lower()
                        for term in (
                            "tarefa administrativa",
                            "tarefas administrativas",
                            "automação administrativa",
                            "automatizar tarefas",
                            "tarefas repetitivas",
                        )
                    )
                    else research.get("problem", "")
                )
            ),

            "target_audience": (
                novelty.get("target_audience")
                or product.get("target_audience")
                or (
                    "Profissionais autônomos que querem reduzir o tempo "
                    "gasto com tarefas administrativas repetitivas."
                    if any(
                        term in (
                            f"{product_name} "
                            f"{product.get('description', '')}"
                        ).lower()
                        for term in (
                            "profissionais autônomos",
                            "profissional autônomo",
                            "tarefas administrativas",
                            "automação administrativa",
                        )
                    )
                    else research.get("target_audience", "")
                )
            ),

            "market": (
                novelty.get("market")
                or product.get("market")
                or research.get("market", "")
            ),

            "product_angle": (
                novelty.get("product_angle")
                or product.get("product_angle")
                or research.get("product_angle", "")
            ),

            "differentiation_strategy": (
                novelty.get("differentiation_strategy")
                or product.get("differentiation_strategy")
                or research.get("differentiation_strategy", "")
            ),

            "unique_mechanism": (
                novelty.get("unique_mechanism")
                or product.get("unique_mechanism")
                or research.get("unique_mechanism", "")
            ),

            "commercial_thesis": (
                novelty.get("commercial_thesis")
                or product.get("commercial_thesis")
                or research.get("commercial_thesis", "")
            ),

            "recommended_format": (
                novelty.get("recommended_format")
                or product.get("recommended_format")
                or product_type
            ),

        }

        # =====================================================
        # 6. CONTEXTO COMERCIAL PARA OTIMIZAÇÃO
        # =====================================================

        optimize_existing = (
            "optimize_offer" in task.lower()
            or "otimizar a oferta" in task.lower()
        )

        commercial_context = {}

        if optimize_existing:
            try:
                import sqlite3

                conn = sqlite3.connect(
                    "digitalfactory.db"
                )
                cursor = conn.cursor()

                row = cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total_orders,
                        SUM(
                            CASE
                                WHEN LOWER(status) = 'paid'
                                THEN 1
                                ELSE 0
                            END
                        ) AS paid_orders,
                        SUM(
                            CASE
                                WHEN LOWER(status) = 'pending'
                                THEN 1
                                ELSE 0
                            END
                        ) AS pending_orders,
                        SUM(
                            CASE
                                WHEN LOWER(status) = 'paid'
                                THEN amount
                                ELSE 0
                            END
                        ) AS revenue
                    FROM orders
                    WHERE product_id = ?
                    """,
                    (product_id,),
                ).fetchone()

                conn.close()

                total_orders = int(row[0] or 0)
                paid_orders = int(row[1] or 0)
                pending_orders = int(row[2] or 0)
                revenue = float(row[3] or 0)

                conversion = (
                    round(
                        (paid_orders / total_orders) * 100,
                        2,
                    )
                    if total_orders
                    else 0.0
                )

                commercial_context = {
                    "product_id": product_id,
                    "metrics": {
                        "total_orders": total_orders,
                        "paid_orders": paid_orders,
                        "pending_orders": pending_orders,
                        "revenue": revenue,
                        "conversion_rate_percent": conversion,
                    },
                    "optimization_goal": (
                        "Melhorar a conversão da oferta existente "
                        "antes de criar qualquer nova variação."
                    ),
                }

            except Exception as exc:
                commercial_context = {
                    "product_id": product_id,
                    "error": str(exc),
                }

        # =====================================================
        # OFERTA ATUAL
        # =====================================================

        existing_offer = None

        if optimize_existing:
            try:
                existing_offer = (
                    sales_engine.get_offer(product_id)
                )
            except Exception:
                existing_offer = None

        if isinstance(existing_offer, dict):
            commercial_context["existing_offer"] = (
                existing_offer
            )

        # =====================================================
        # 7. CRIAR / OTIMIZAR OFERTA
        # =====================================================

        offer = await offer_engine.create_offer(
            product=offer_product,
            research=research,
            novelty=novelty,
            commercial_context=commercial_context,
            optimize_existing=optimize_existing,
        )

        if not isinstance(
            offer,
            dict
        ):

            return {
                "status": "failed",
                "agent": self.name,
                "task": task,
                "product_id": product_id,
                "message": (
                    "Offer Engine não retornou "
                    "uma oferta válida."
                ),
            }


        # =====================================================
        # REGISTRO: OFERTA CRIADA
        # =====================================================

        try:
            publication_tracker.log_activity(
                activity_type="offer_created",
                product_id=product_id,
                title="Oferta comercial criada",
                description=(
                    f"Oferta criada para o produto "
                    f"'{product_name}'."
                ),
                status="completed",
                metadata={
                    "offer_name": offer.get("offer_name"),
                    "price": offer.get("price"),
                    "currency": offer.get("currency"),
                },
            )
        except Exception:
            pass

        # =====================================================
        # 7. PUBLICAR ATRAVÉS DO SALES ENGINE
        # =====================================================

        publication = sales_engine.publish(
            product_id=product_id,
            offer=offer,
        )


        # =====================================================
        # REGISTRO: PUBLICAÇÃO
        # =====================================================

        try:

            publication_status = (
                publication.get("status")
                if isinstance(publication, dict)
                else "unknown"
            )

            publication_tracker.create_publication(
                product_id=product_id,
                channel="digitalfactory",
                status=(
                    "published"
                    if publication_status == "published"
                    else "prepared"
                ),
                title=product_name,
                content=offer.get("sales_copy"),
                source="internal",
                campaign="autonomous_factory",
                medium="sales_page",
            )

            publication_tracker.log_activity(
                activity_type="publication",
                product_id=product_id,
                title="Página de venda processada",
                description=(
                    f"A página de venda do produto "
                    f"'{product_name}' foi processada pelo Sales Engine."
                ),
                status=publication_status or "unknown",
                metadata={
                    "channel": "digitalfactory",
                    "publication_status": publication_status,
                },
            )

        except Exception:
            pass

        # =====================================================
        # 8. PÁGINA DE VENDAS
        # =====================================================

        sales_page = sales_engine.sales_page(
            product_id=product_id
        )

        # =====================================================
        # 9. CHECKOUT
        # =====================================================

        checkout = sales_engine.checkout_info(
            product_id=product_id
        )

        # =====================================================
        # 10. RESULTADO
        # =====================================================

        publication_status = (
            publication.get(
                "status"
            )
            if isinstance(
                publication,
                dict
            )
            else None
        )

        if publication_status == "published":

            status = "success"

            message = (
                "Oferta criada pelo Offer Engine, "
                "aprovada pelo Sales Engine e "
                "produto preparado para venda."
            )

        elif publication_status == "blocked":

            status = "blocked"

            message = (
                "Oferta criada, mas bloqueada "
                "pelo quality gate comercial."
            )

        else:

            status = "failed"

            message = (
                "A oferta foi criada, mas o "
                "produto não foi publicado."
            )

        result = {

            "status": status,

            "agent": self.name,

            "task": task,

            "product": {

                "id": product_id,

                "name": product_name,

                "type": product_type,

                "price": price,

                "currency": currency,

            },

            "offer": offer,

            "publication": publication,

            "sales_page": sales_page,

            "checkout": checkout,

            "product_memory_used": (
                product
            ),

            "research_memory_used": (
                research_context
            ),

            "knowledge_used": (
                knowledge_context
            ),

            "message": message,

        }

        # =====================================================
        # 11. MEMÓRIA
        # =====================================================

        memory.save(

            agent=self.name,

            task=task,

            status=status,

            result=result

        )

        # =====================================================
        # 12. CONHECIMENTO
        # =====================================================

        knowledge.add(

            agent=self.name,

            knowledge={

                "type": "commercial_offer",

                "product_id": product_id,

                "product_name": product_name,

                "offer": offer,

                "publication": publication,

            }

        )

        return result


marketing_agent = MarketingAgent()
