import os
import json

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


    def _fallback_research(self, task: str):

        return {
            "problem": (
                "Pessoas e pequenos negócios têm dificuldade "
                "em transformar conhecimento ou uma necessidade "
                "específica em uma solução digital simples."
            ),

            "target_audience": (
                "Pessoas que querem aprender uma habilidade prática "
                "ou resolver um problema específico através de "
                "um produto digital de baixo custo."
            ),

            "niche": (
                "Educação prática e soluções digitais simples."
            ),

            "market_need": (
                "Existe necessidade de materiais objetivos, "
                "práticos e fáceis de consumir que ajudem o "
                "cliente a alcançar um resultado específico."
            ),

            "opportunity": (
                "Criar produtos digitais pequenos e específicos, "
                "com promessa clara de resultado e baixo custo "
                "de produção."
            ),

            "recommended_product": (
                "Ebook ou guia prático focado em resolver "
                "um problema específico."
            ),

            "recommended_format": (
                "Ebook PDF acompanhado de checklist e plano de ação."
            ),

            "suggested_price": (
                "US$ 9,90 a US$ 19,90 para mercado internacional; "
                "R$ 29,90 a R$ 59,90 para o mercado brasileiro."
            ),

            "differential": (
                "Conteúdo objetivo, aplicação prática, "
                "checklists e orientação passo a passo."
            ),

            "validation_strategy": (
                "Publicar uma oferta simples, testar a aceitação "
                "através de tráfego orgânico e medir interesse, "
                "cliques, pedidos e vendas antes de aumentar "
                "o investimento."
            ),

            "confidence": (
                "Hipótese inicial. Validar com clientes reais."
            ),

            "research_mode": "fallback_local"
        }


    async def execute_task(self, task: str):

        research = None
        research_mode = None


        # ==========================================
        # Tentar pesquisa com OpenAI
        # ==========================================

        if self.client:

            prompt = f"""
Você é o ResearchAgent do DigitalFactoryAI.

Sua função é analisar oportunidades de produtos digitais
com potencial comercial.

OBJETIVO RECEBIDO:
{task}

Analise o objetivo e produza uma pesquisa estruturada.

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
