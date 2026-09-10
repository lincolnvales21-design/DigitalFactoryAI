
import json
import os
from datetime import datetime

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class OfferEngine:
    """
    Transforma um produto em uma oferta comercial estruturada.

    O motor não movimenta dinheiro.
    Ele cria posicionamento, promessa, benefícios, preço,
    copy e chamada para ação.
    """

    def _fallback(
        self,
        product,
        research=None,
        novelty=None,
        commercial_context=None,
        optimize_existing=False,
    ):
        product = product or {}
        research = research or {}
        novelty = novelty or {}

        commercial_context = (
            commercial_context
            if isinstance(commercial_context, dict)
            else {}
        )

        metrics = commercial_context.get(
            "metrics",
            {}
        )

        total_orders = int(
            metrics.get("total_orders", 0) or 0
        )

        paid_orders = int(
            metrics.get("paid_orders", 0) or 0
        )

        pending_orders = int(
            metrics.get("pending_orders", 0) or 0
        )

        revenue = float(
            metrics.get("revenue", 0) or 0
        )

        conversion = float(
            metrics.get(
                "conversion_rate_percent",
                0
            ) or 0
        )

        existing_offer = commercial_context.get(
            "existing_offer"
        )

        title = (
            product.get("title")
            or "Solução Digital Prática"
        )

        description = (
            product.get("description")
            or ""
        )

        # =====================================================
        # CONTEXTO COMERCIAL CANÔNICO
        # Produto/Radar têm prioridade.
        # ResearchAgent é apenas fallback.
        # =====================================================

        audience = (
            product.get("target_audience")
            or research.get("target_audience")
            or novelty.get("target_audience")
            or "pessoas que precisam resolver esse problema"
        )

        problem = (
            product.get("problem")
            or research.get("problem")
            or "um problema específico"
        )

        differentiation = (
            product.get("differentiation_strategy")
            or research.get("differentiation_strategy")
            or novelty.get("differentiation_strategy")
            or "orientação prática e estruturada"
        )

        product_angle = (
            product.get("product_angle")
            or research.get("product_angle")
            or novelty.get("product_angle")
            or ""
        )

        mechanism = (
            product.get("unique_mechanism")
            or research.get("unique_mechanism")
            or novelty.get("unique_mechanism")
            or "método estruturado orientado ao problema específico"
        )

        commercial_thesis = (
            product.get("commercial_thesis")
            or research.get("commercial_thesis")
            or novelty.get("commercial_thesis")
            or ""
        )

        if optimize_existing and total_orders > 0:

            commercial_thesis = (
                f"Oferta com evidência comercial real: "
                f"{paid_orders} venda(s) confirmada(s) em "
                f"{total_orders} pedido(s), "
                f"receita de R$ {revenue:.2f} e "
                f"conversão de {conversion:.2f}%. "
                f"Priorizar melhoria da conversão sem "
                f"alterar o produto."
            )

        price = product.get("price")

        if not price:
            price = 29.90

        return {
            "status": "created",

            "offer_name": title,

            "positioning": (
                (
                    f"Oferta otimizada para {audience}, "
                    f"com foco em {problem} e melhoria "
                    f"da conversão."
                )
                if optimize_existing and total_orders > 0
                else (
                    f"Solução prática para {audience}, "
                    f"voltada para {problem}."
                )
            ),

            "promise": (
                f"Ajudar {audience} a organizar e executar "
                f"uma abordagem prática para {problem}."
            ),

            "core_benefit": (
                f"Usar {mechanism} para lidar com "
                f"{problem} de forma clara e estruturada."
            ),

            "benefits": [
                f"Aplicação prática para {problem}",
                f"Orientação específica para {audience}",
                "Passo a passo estruturado",
                "Checklists e materiais de apoio",
                f"Mecanismo: {mechanism}",
            ],

            "differentiator": (
                f"{differentiation}"
                + (
                    f" Ângulo: {product_angle}."
                    if product_angle
                    else ""
                )
            ),

            "unique_mechanism": mechanism,

            "commercial_thesis": commercial_thesis,

            "offer_stack": [
                "Produto principal",
                "Checklist de implementação",
                "Plano de ação",
                "Material complementar",
            ],

            "price": price,

            "currency": product.get(
                "currency",
                "BRL"
            ),

            "sales_copy": (
                (
                    f"{title}\n\n"
                    f"Uma solução prática para {problem}.\n\n"
                    f"Desenvolvida para {audience}, "
                    f"com foco em execução e resultado.\n\n"
                    f"Esta oferta foi otimizada com base "
                    f"no desempenho comercial observado."
                )
                if optimize_existing and total_orders > 0
                else (
                    f"{title}\n\n"
                    f"Uma solução prática para {problem}.\n\n"
                    f"Desenvolvida para {audience}, "
                    f"com foco em execução e resultado."
                )
            ),

            "cta": "Quero começar agora",

            "urgency": (
                "Comece agora e transforme o problema "
                "em um plano de ação."
            ),

            "objection_handling": [
                {
                    "objection": "Não tenho tempo.",
                    "response": (
                        "A solução foi estruturada em etapas "
                        "curtas e práticas."
                    )
                },
                {
                    "objection": "Não sei por onde começar.",
                    "response": (
                        "O método organiza o caminho desde "
                        "o diagnóstico inicial."
                    )
                },
                {
                    "objection": "Será que funciona para mim?",
                    "response": (
                        "A proposta é orientada ao problema "
                        "e ao perfil específico do público."
                    )
                }
            ],

            "traffic_angles": [
                "Problema específico",
                "Erro comum",
                "Antes e depois",
                "Passo prático",
                "Diagnóstico",
                "Checklist gratuito",
            ],

            "validation_plan": [
                "Publicar conteúdo relacionado ao problema.",
                "Observar interesse e interação.",
                "Apresentar a oferta.",
                "Medir cliques.",
                "Medir conversões.",
                "Ajustar a oferta com base nos dados.",
            ],

            "generated_at": datetime.utcnow().isoformat(),
        }

    async def create_offer(
        self,
        product,
        research=None,
        novelty=None,
        commercial_context=None,
        optimize_existing=False,
    ):
        fallback = self._fallback(
            product,
            research,
            novelty,
            commercial_context=commercial_context,
            optimize_existing=optimize_existing,
        )

        commercial_context = (
            commercial_context
            if isinstance(commercial_context, dict)
            else {}
        )

        api_key = os.getenv("OPENAI_API_KEY")

        if not (OpenAI and api_key):
            return fallback

        prompt = f"""
Você é o Offer Engine do DigitalFactoryAI.

Transforme este produto em uma oferta comercial forte.

PRODUTO:
{json.dumps(product, ensure_ascii=False, indent=2)}

PESQUISA:
{json.dumps(research or {}, ensure_ascii=False, indent=2)}

NOVIDADE:
{json.dumps(novelty or {}, ensure_ascii=False, indent=2)}

Crie:

offer_name
positioning
promise
core_benefit
benefits
differentiator
offer_stack
sales_copy
cta
urgency
objection_handling
traffic_angles
validation_plan

CONTEXTO COMERCIAL REAL:
{json.dumps(commercial_context, ensure_ascii=False, indent=2)}

MODO DE OPERAÇÃO:
{"OTIMIZAÇÃO DA OFERTA EXISTENTE" if optimize_existing else "CRIAÇÃO DA OFERTA"}

Se o modo for OTIMIZAÇÃO DA OFERTA EXISTENTE:
- Melhorar a oferta comercial existente em vez de criar outro produto.
- Usar os dados comerciais fornecidos como fatos.
- Priorizar conversão, clareza da promessa, benefícios, objeções, copy e CTA.
- Não inventar novas vendas, receita, conversões, depoimentos ou resultados.
- Não alterar o produto físico/digital em si.
- Não aumentar produção.
- Não criar uma nova variação de produto.
- Manter o problema central e o público identificado.
- Preservar o preço atual salvo se existir evidência comercial explícita para outra decisão.
- A melhoria deve responder aos obstáculos comerciais observados.

Regras gerais:
- Não inventar depoimentos.
- Não inventar resultados.
- Não prometer cura.
- Não afirmar exclusividade mundial.
- Não usar falsas garantias.
- Escrever para venda real.
- Ser específico.
- Destacar o diferencial.
- Priorizar clareza.
- A oferta deve ser adequada ao público identificado.

Retorne SOMENTE JSON.
"""

        try:
            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é especialista em ofertas "
                            "e posicionamento comercial."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.75,
            )

            result = json.loads(
                response.choices[0].message.content.strip()
            )

            if not isinstance(result, dict):
                return fallback

            result["status"] = "created"
            result["generated_at"] = datetime.utcnow().isoformat()

            return result

        except Exception:
            return fallback


offer_engine = OfferEngine()
