from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge
from app.products.generator import product_generator
from app.database.database import get_connection
from app.pricing.pricing_engine import PricingEngine
from app.products.factory import product_factory


pricing_engine = PricingEngine()


class ProductAgent(BaseAgent):

    def __init__(self):

        super().__init__("ProductAgent")

        self.add_capability("product_creation")
        self.add_capability("ebook")
        self.add_capability("course")
        self.add_capability("digital_product")


    def _commercial_product_name(self, research, radar_context):
        """
        Gera nome específico a partir do problema, público e mecanismo.
        Evita nomes genéricos e não depende do fallback de ebook.
        """

        problem = (
            radar_context.get("problem")
            or research.get("problem")
            or "resolver um problema específico"
        ).strip()

        audience = (
            radar_context.get("target_audience")
            or research.get("target_audience")
            or "profissionais"
        ).strip()

        area = (
            radar_context.get("area")
            or research.get("area")
            or "negócios"
        ).strip()

        mechanism = (
            radar_context.get("unique_mechanism")
            or research.get("unique_mechanism")
            or "sistema prático"
        ).strip()

        problem_clean = problem.rstrip(". ")
        audience_clean = audience.rstrip(". ")
        mechanism_clean = mechanism.rstrip(". ")

        # Nomes específicos por padrões comerciais.
        if "conteúdo comercial" in problem_clean.lower():
            return (
                "Autoridade em Conteúdo — "
                f"Sistema para {audience_clean} transformar conhecimento em conteúdo comercial"
            )

        if "tarefas administrativas" in problem_clean.lower():
            return (
                "Automação Administrativa IA — "
                f"Sistema para {audience_clean} automatizarem tarefas repetitivas"
            )

        if "atendimento comercial" in problem_clean.lower():
            return (
                "Atendimento que Converte — "
                f"Sistema comercial para {audience_clean}"
            )

        if "transição profissional" in problem_clean.lower():
            return (
                "Rota de Transição Profissional — "
                f"Plano prático para {audience_clean}"
            )

        if "decisões financeiras" in problem_clean.lower():
            return (
                "Decisão Financeira Clara — "
                f"Sistema prático para {audience_clean}"
            )

        if "sistema de estudo" in problem_clean.lower():
            return (
                "Estudo em Sistema — "
                f"Framework prático para {audience_clean}"
            )

        # Fallback comercial seguro.
        # Nunca montar frases com "resolverem + verbo",
        # pois isso gera nomes gramaticalmente quebrados.
        problem_lower = problem_clean.lower()

        if "reduzir erros de atendimento" in problem_lower:
            return (
                "Atendimento sem Erros — "
                "Sistema de Respostas Comerciais para Pequenos Negócios"
            )

        if "rotina sustentável" in problem_lower:
            return (
                "Rotina Sustentável — "
                "Planner de Organização para Profissionais com Rotina Intensa"
            )

        if "decisões repetitivas" in problem_lower:
            return (
                "Semana sem Sobrecarga — "
                "Sistema de Organização para Pessoas com Muitas Responsabilidades"
            )

        if "decisões financeiras" in problem_lower:
            return (
                "Decisão Financeira Clara — "
                "Sistema Prático para Adultos com Renda Variável"
            )

        if "transição profissional" in problem_lower:
            return (
                "Rota de Transição Profissional — "
                f"Plano Prático para {audience_clean}"
            )

        if "sistema de estudo" in problem_lower:
            return (
                "Estudo em Sistema — "
                f"Framework Prático para {audience_clean}"
            )

        return (
            f"{area.title()} em Ação — "
            f"Sistema Prático para {audience_clean}"
        )

    async def execute_task(self, task: str):

        # =====================================================
        # 1. CONTEXTO DA PESQUISA
        # =====================================================

        research_context = memory.get_latest_result(
            "ResearchAgent"
        )

        if not research_context:

            return {
                "status": "error",
                "agent": self.name,
                "task": task,
                "message": (
                    "Nenhuma pesquisa do ResearchAgent encontrada."
                ),
            }

        # =====================================================
        # 2. EXTRAIR PESQUISA
        # =====================================================

        if isinstance(research_context, dict):

            research = research_context.get(
                "research",
                research_context,
            )

        else:

            research = {}

        if not isinstance(research, dict):

            research = {}

        # =====================================================
        # 3. EXTRAIR CONTEXTO DO RADAR
        # =====================================================

        # O Radar define a oportunidade comercial.
        # O ResearchAgent é contexto de apoio.
        # Portanto, os campos fundamentais do Radar têm prioridade.

        radar_context = {}

        radar_markers = {
            "Área:": "area",
            "Problema:": "problem",
            "Público:": "target_audience",
            "Formato recomendado:": "recommended_format",
            "Mercado:": "market",
            "Ângulo do produto:": "product_angle",
            "Diferenciação:": "differentiation_strategy",
            "Mecanismo:": "unique_mechanism",
            "Tese comercial:": "commercial_thesis",
            "Decisão comercial:": "decision",
        }

        marker_positions = []

        task_lower = task.lower()

        for marker, key in radar_markers.items():

            marker_lower = marker.lower()

            position = task_lower.find(marker_lower)

            if position >= 0:

                marker_positions.append(
                    (
                        position,
                        marker,
                        key,
                    )
                )

        marker_positions.sort(
            key=lambda item: item[0]
        )

        for index, (position, marker, key) in enumerate(
            marker_positions
        ):

            start_value = position + len(marker)

            if index + 1 < len(marker_positions):

                end_value = marker_positions[index + 1][0]

            else:

                end_value = len(task)

            value = task[start_value:end_value].strip()

            value = value.strip(" .,:;")

            if value:

                radar_context[key] = value

        if radar_context:

            research = {
                **research,
                **radar_context,
            }

        commercial_context = {}

        for key in (
            "product_angle",
            "differentiation_strategy",
            "unique_mechanism",
            "commercial_thesis",
        ):
            if key in radar_context:
                commercial_context[key] = radar_context[key]
            elif research.get(key):
                commercial_context[key] = research.get(key)

        if commercial_context:

            research = {
                **research,
                **commercial_context,
            }

        # =====================================================
        # 6. CONHECIMENTO PERSISTENTE
        # =====================================================

        knowledge_context = knowledge.latest()

        # =====================================================
        # 7. DEFINIÇÃO DO PRODUTO
        # =====================================================

        # =====================================================
        # RADAR = FONTE PRINCIPAL DA OPORTUNIDADE
        # =====================================================

        problem = (
            radar_context.get("problem")
            or research.get(
                "problem",
                "Problema não definido",
            )
        )

        target_audience = (
            radar_context.get("target_audience")
            or research.get(
                "target_audience",
                "Público-alvo não definido",
            )
        )

        area = (
            radar_context.get("area")
            or research.get(
                "area",
                "mercado digital",
            )
        )

        market = (
            radar_context.get("market")
            or research.get("market", "")
        )

        niche = research.get(
            "niche"
        ) or area

        # Mantém o contexto comercial do Radar dentro
        # do research usado pelos motores seguintes.
        research = {
            **research,
            "area": area,
            "problem": problem,
            "target_audience": target_audience,
            "market": market,
        }

        recommended_product = research.get(
            "recommended_product",
            "Solução digital prática",
        )

        # =====================================================
        # 8. FORMATO ESCOLHIDO PELO RADAR
        # =====================================================

        radar_format = radar_context.get(
            "recommended_format"
        )

        if radar_format:

            product_format = (
                product_factory.normalize_format(
                    radar_format
                )
            )

        else:

            product_format = (
                product_factory.choose_format(
                    research=research,
                    novelty=research,
                )
            )

        # =====================================================
        # 9. QUALITY GATE
        # =====================================================

        # O AutonomousBusinessEngine só envia o produto para
        # produção depois da aprovação do NoveltyEngine.
        # Ainda assim, enviamos a decisão explicitamente para
        # a ProductFactory.

        decision = (
            radar_context.get("decision")
            or "ready_for_product_creation"
        )

        novelty_context = {
            "decision": decision,
            "status": decision,
            "area": area,
            "problem": problem,
            "target_audience": target_audience,
            "recommended_format": (
                radar_context.get(
                    "recommended_format"
                )
                or product_format
            ),
            "market": (
                radar_context.get("market")
                or research.get("market")
                or ""
            ),
            "product_angle": research.get(
                "product_angle",
                "",
            ),
            "differentiation_strategy": research.get(
                "differentiation_strategy",
                "",
            ),
            "unique_mechanism": research.get(
                "unique_mechanism",
                "",
            ),
            "commercial_thesis": research.get(
                "commercial_thesis",
                "",
            ),
        }

        # =====================================================
        # 10. PREÇO
        # =====================================================

        pricing = pricing_engine.calculate(
            research=research,
            task=task,
        )

        price = pricing["price"]
        currency = pricing["currency"]

        print(
            "DEBUG PRICING:",
            pricing,
        )

        # =====================================================
        # 11. PRÉ-DEFINIÇÃO DO PRODUTO
        # =====================================================

        # =====================================================
        # NOME COMERCIAL ESPECÍFICO
        # =====================================================

        product_title = self._commercial_product_name(
            research=research,
            radar_context=radar_context,
        )

        # O título comercial definido pelo ProductAgent
        # passa a ser a fonte oficial para a ProductFactory.
        research["product_title"] = product_title

        product_description = (
            product_factory.build_description(
                research=research,
                novelty=novelty_context,
                product_format=product_format,
            )
        )

        # =====================================================
        # 12. REGISTRAR PRODUTO
        # =====================================================

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO products (
                name,
                description,
                product_type,
                price,
                currency,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product_title,
                product_description,
                product_format,
                price,
                currency,
                "draft",
            ),
        )

        product_id = cursor.lastrowid

        connection.commit()
        connection.close()

        # =====================================================
        # 13. PRODUCT FACTORY
        # =====================================================

        factory_result = (
            product_factory.create_artifact(
                product_id=product_id,
                research=research,
                novelty=novelty_context,
                product_format=product_format,
            )
        )

        # =====================================================
        # 14. COMPATIBILIDADE COM GERADOR ANTIGO
        # =====================================================

        legacy_generated = None

        factory_approved = (
            factory_result.get("status") == "success"
            and factory_result.get(
                "quality_gate",
                {},
            ).get("status") == "approved"
        )

        if product_format == "ebook" and factory_approved:

            try:

                legacy_generated = (
                    product_generator.create_ebook(
                        title=product_title,
                        research=research,
                        product_id=product_id,
                    )
                )

            except Exception as exc:

                legacy_generated = {
                    "status": "compatibility_error",
                    "error": str(exc),
                }

        # =====================================================
        # 15. RESULTADO
        # =====================================================

        product_status = (
            "draft"
            if factory_approved
            else "blocked"
        )

        result_status = (
            "success"
            if factory_approved
            else "blocked"
        )

        result = {

            "status": result_status,

            "agent": self.name,

            "task": task,

            "product_id": product_id,

            "product": {

                "id": product_id,

                "name": product_title,

                "type": product_format,

                "price": price,

                "currency": currency,

                "status": product_status,

                "artifact": factory_result.get(
                    "artifact"
                ),

                "factory_status": factory_result.get(
                    "status"
                ),

            },

            "product_definition": {

                "area": area,

                "problem": problem,

                "target_audience": target_audience,

                "niche": niche,

                "recommended_product": (
                    recommended_product
                ),

                "selected_format": product_format,

                "radar_format": radar_format,

                "market": novelty_context.get(
                    "market",
                    "",
                ),

                "product_angle": research.get(
                    "product_angle",
                    "",
                ),

                "differentiation_strategy": research.get(
                    "differentiation_strategy",
                    "",
                ),

                "unique_mechanism": research.get(
                    "unique_mechanism",
                    "",
                ),

                "commercial_thesis": research.get(
                    "commercial_thesis",
                    "",
                ),

                "commercial_decision": decision,

            },

            "factory": factory_result,

            "legacy_ebook_generator": (
                legacy_generated
            ),

            "research_memory_used": (
                research_context
            ),

            "knowledge_used": (
                knowledge_context
            ),

            "message": (
                "Produto digital criado e aprovado "
                "pela ProductFactory."
                if factory_approved
                else
                "Produto registrado, mas bloqueado "
                "pela ProductFactory."
            ),
        }

        # =====================================================
        # 16. MEMÓRIA
        # =====================================================

        memory.save(

            agent=self.name,

            task=task,

            status=(
                "completed"
                if factory_approved
                else "blocked"
            ),

            result=result,
        )

        return result


product_agent = ProductAgent()
