import os
import json
import re
import sqlite3

from openai import OpenAI

from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge


class ResearchAgent(BaseAgent):

    def __init__(self):

        super().__init__("ResearchAgent")

        self.add_capability("market_research")
        self.add_capability("niche_analysis")
        self.add_capability("trend_analysis")

        api_key = os.getenv("OPENAI_API_KEY")

        self.client = (
            OpenAI(api_key=api_key)
            if api_key
            else None
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini"
        )


    def _get_commercial_data(self, task: str):
        """
        Consulta os dados comerciais reais do produto mencionado
        na tarefa de validação.
        """

        match = re.search(
            r"produto #([0-9]+)",
            task,
            re.IGNORECASE,
        )

        if not match:
            return None

        product_id = int(match.group(1))

        db_path = os.getenv(
            "DIGITALFACTORY_DB",
            "digitalfactory.db",
        )

        try:
            connection = sqlite3.connect(
                db_path
            )
            connection.row_factory = sqlite3.Row

            cursor = connection.cursor()

            product = cursor.execute(
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
                (product_id,),
            ).fetchone()

            if product is None:
                connection.close()
                return None

            orders = cursor.execute(
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

            connection.close()

            total_orders = int(
                orders["total_orders"] or 0
            )

            paid_orders = int(
                orders["paid_orders"] or 0
            )

            pending_orders = int(
                orders["pending_orders"] or 0
            )

            revenue = float(
                orders["revenue"] or 0
            )

            conversion_rate = (
                round(
                    (paid_orders / total_orders) * 100,
                    2,
                )
                if total_orders
                else 0.0
            )

            return {
                "product_id": product_id,
                "product": {
                    "name": product["name"],
                    "description": product["description"],
                    "product_type": product["product_type"],
                    "price": product["price"],
                    "currency": product["currency"],
                    "status": product["status"],
                    "created_at": product["created_at"],
                },
                "commercial_metrics": {
                    "total_orders": total_orders,
                    "paid_orders": paid_orders,
                    "pending_orders": pending_orders,
                    "revenue": revenue,
                    "conversion_rate_percent": conversion_rate,
                },
            }

        except Exception as exc:
            return {
                "error": str(exc),
                "product_id": product_id,
            }


    def _fallback_research(self, task: str):

        task_text = str(task or "").strip()
        lower = task_text.lower()

        problem = (
            "Profissionais autônomos perdem tempo com "
            "tarefas administrativas repetitivas que poderiam "
            "ser simplificadas ou automatizadas."
        )

        target_audience = "Profissionais autônomos."

        if "autônom" in lower:
            target_audience = "Profissionais autônomos."

        if (
            "administrativ" in lower
            or "tarefa repetitiva" in lower
            or "automatizar" in lower
            or "automação" in lower
        ):
            problem = (
                "Profissionais autônomos perdem tempo com "
                "tarefas administrativas repetitivas e precisam "
                "de uma forma simples de identificar, organizar "
                "e automatizar essas tarefas usando inteligência artificial."
            )

        if "curso" in lower:
            recommended_product = (
                "Curso curto e prático ensinando profissionais "
                "autônomos a identificar e automatizar tarefas "
                "administrativas repetitivas com inteligência artificial."
            )
            recommended_format = "Curso curto dividido em módulos práticos."
        elif "ebook" in lower:
            recommended_product = (
                "Ebook prático sobre automação de tarefas "
                "administrativas repetitivas com inteligência artificial."
            )
            recommended_format = (
                "Ebook PDF acompanhado de checklist e plano de ação."
            )
        else:
            recommended_product = (
                "Produto digital prático para ajudar profissionais "
                "autônomos a automatizar tarefas administrativas repetitivas."
            )
            recommended_format = "Curso curto ou guia prático."

        return {
            "problem": problem,

            "target_audience": target_audience,

            "niche": (
                "Automação de tarefas administrativas com inteligência artificial."
            ),

            "market_need": (
                "Profissionais autônomos precisam reduzir o tempo gasto "
                "em tarefas repetitivas e organizar melhor sua rotina."
            ),

            "opportunity": (
                "Ensinar uma forma prática de identificar tarefas "
                "repetitivas, escolher o que automatizar e criar "
                "fluxos simples usando inteligência artificial."
            ),

            "recommended_product": recommended_product,

            "recommended_format": recommended_format,

            "suggested_price": (
                "R$ 14,90 a R$ 49,90 para validação inicial no Brasil."
            ),

            "differential": (
                "Conteúdo objetivo, aplicação prática, "
                "exemplos, checklists e orientação passo a passo."
            ),

            "validation_strategy": (
                "Publicar uma oferta simples, medir alcance, "
                "cliques, pedidos e vendas e usar os resultados "
                "para decidir a próxima otimização."
            ),

            "confidence": (
                "Hipótese inicial baseada no contexto disponível. "
                "Validar com clientes reais."
            ),

            "research_mode": "fallback_local",
        }


    async def execute_task(self, task: str):

        research = None
        research_mode = None

        commercial_data = None

        if (
            "validate_product" in task.lower()
            or "validar comercialmente" in task.lower()
        ):
            commercial_data = (
                self._get_commercial_data(task)
            )


        # ==========================================
        # Tentar pesquisa com OpenAI
        # ==========================================

        if self.client:

            commercial_context = ""

            if commercial_data:
                commercial_context = f"""
DADOS COMERCIAIS REAIS DO PRODUTO:

{json.dumps(
    commercial_data,
    ensure_ascii=False,
    indent=2,
)}

Use estes dados como fatos observados.
Não invente métricas adicionais.
"""

            prompt = f"""
Você é o ResearchAgent do DigitalFactoryAI.

Sua função é analisar oportunidades de produtos digitais
com potencial comercial.

OBJETIVO RECEBIDO:
{task}

{commercial_context}

Analise o objetivo e produza uma pesquisa estruturada.

Quando houver DADOS COMERCIAIS REAIS:
- baseie a validação nesses dados;
- diferencie fatos observados de hipóteses;
- avalie conversão, pedidos pendentes e receita;
- identifique obstáculos comerciais;
- proponha ações práticas de melhoria;
- priorize melhorar o produto existente antes de criar outro.

Procure identificar:

1. Problema principal
2. Público-alvo
3. Nicho
4. Necessidade do mercado
5. Possível oportunidade comercial
6. Produto digital recomendado
7. Formato recomendado
8. Faixa de preço sugerida
9. Diferencial da oferta
10. Estratégia inicial de validação

IMPORTANTE:

- Não invente dados estatísticos específicos.
- Quando uma informação não puder ser confirmada,
  trate-a como hipótese.
- Priorize oportunidades simples de executar.
- Considere Brasil e mercado internacional quando isso
  fizer parte do objetivo.
- O resultado será utilizado pelo ProductAgent e
  pelo MarketingAgent.

Responda SOMENTE em JSON válido.

Formato:

{{
    "problem": "...",
    "target_audience": "...",
    "niche": "...",
    "market_need": "...",
    "opportunity": "...",
    "recommended_product": "...",
    "recommended_format": "...",
    "suggested_price": "...",
    "differential": "...",
    "validation_strategy": "...",
    "confidence": "..."
}}
"""

            try:

                response = self.client.responses.create(
                    model=self.model,
                    input=prompt
                )

                content = response.output_text.strip()

                try:

                    research = json.loads(content)

                except json.JSONDecodeError:

                    research = {
                        "raw_analysis": content
                    }

                research_mode = "openai"

            except Exception as e:

                print(
                    "ResearchAgent: OpenAI indisponível. "
                    "Usando fallback local."
                )

                print(
                    f"ResearchAgent OpenAI error: {e}"
                )


        # ==========================================
        # Fallback sem custo
        # ==========================================

        if research is None:

            research = self._fallback_research(
                task
            )

            research_mode = "fallback_local"


        # ==========================================
        # Resultado
        # ==========================================

        result = {

            "status": "success",

            "agent": self.name,

            "task": task,

            "research": research,

            "research_mode": research_mode,

            "commercial_data": commercial_data,

            "message": (
                "Pesquisa de mercado concluída."
            )
        }


        # ==========================================
        # Memória
        # ==========================================

        memory.save(

            agent=self.name,

            task=task,

            status="completed",

            result=result

        )


        # ==========================================
        # Conhecimento persistente
        # ==========================================

        knowledge.add(

            agent=self.name,

            knowledge={

                "type": "market_research",

                "topic": task,

                "research": research,

                "research_mode": research_mode

            }

        )


        return result
