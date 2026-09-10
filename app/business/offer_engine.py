
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

        metrics = commercial_context.get("metrics", {})

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
            metrics.get("conversion_rate_percent", 0) or 0
        )

        existing_offer = commercial_context.get(
            "existing_offer"
        )

        if not isinstance(existing_offer, dict):
            existing_offer = {}

        title = (
            product.get("title")
            or product.get("name")
            or existing_offer.get("offer_name")
            or "Produto Digital"
        )

        description = (
            product.get("description")
            or ""
        ).strip()

        audience = (
            product.get("target_audience")
            or product.get("audience")
            or existing_offer.get("target_audience")
            or "pessoas que buscam uma solução prática"
        )

        problem = (
            product.get("problem")
            or existing_offer.get("problem")
            or description
            or "um problema específico"
        )

        mechanism = (
            product.get("unique_mechanism")
            or existing_offer.get("unique_mechanism")
            or "método prático e estruturado"
        )

        if optimize_existing and total_orders > 0:
            offer_name = (
                existing_offer.get("offer_name")
                or title
            )

            positioning = (
                f"{offer_name} posicionada como uma solução "
                f"prática para {audience}, com foco em "
                f"resolver {problem} e aumentar a conversão."
            )

            promise = (
                f"Ajudar {audience} a resolver {problem} "
                f"de forma prática, clara e estruturada."
            )

            core_benefit = (
                f"Aplicar {mechanism} para transformar "
                f"{problem} em um plano de ação."
            )

            benefits = [
                f"Aplicação prática para resolver {problem}.",
                f"Orientação direcionada para {audience}.",
                "Passo a passo estruturado.",
                "Checklist de implementação.",
                "Plano de ação para colocar o método em prática.",
            ]

            sales_copy = (
                f"{offer_name}\n\n"
                f"{promise}\n\n"
                f"Desenvolvido para {audience}.\n\n"
                f"Você recebe:\n"
                f"• {benefits[0]}\n"
                f"• {benefits[1]}\n"
                f"• {benefits[2]}\n"
                f"• {benefits[3]}\n"
                f"• {benefits[4]}\n\n"
                f"Esta oferta está sendo otimizada com base "
                f"em dados comerciais reais."
            )

            commercial_thesis = (
                f"O produto possui {paid_orders} venda(s) "
                f"confirmada(s) em {total_orders} pedido(s), "
                f"com receita de R$ {revenue:.2f} e conversão "
                f"de {conversion:.2f}%. "
                f"Existem {pending_orders} pedido(s) pendente(s), "
                f"que não são contabilizados como receita. "
                f"O sinal comercial é positivo, porém a amostra "
                f"ainda é pequena. Prioridade: otimizar oferta "
                f"e conversão antes de criar novas variações."
            )

            cta = (
                existing_offer.get("cta")
                or "Quero começar agora"
            )

            urgency = (
                f"Comece agora e transforme {problem} "
                f"em um plano de ação."
            )

            objection_handling = [
                {
                    "objection": "Não tenho tempo.",
                    "response": (
                        "A solução foi organizada em etapas "
                        "curtas e práticas."
                    ),
                },
                {
                    "objection": "Não sei por onde começar.",
                    "response": (
                        "O método apresenta um caminho "
                        "estruturado para começar."
                    ),
                },
                {
                    "objection": "Será que funciona para mim?",
                    "response": (
                        f"A proposta foi construída para "
                        f"{audience} e focada em {problem}."
                    ),
                },
            ]

            traffic_angles = [
                f"Como resolver {problem}",
                "Erro comum",
                "Antes e depois",
                "Passo prático",
                "Diagnóstico",
                "Checklist gratuito",
            ]

            validation_plan = [
                "Publicar conteúdo relacionado ao problema.",
                "Observar interesse e interação.",
                "Apresentar a oferta otimizada.",
                "Medir cliques.",
                "Medir conversões.",
                "Ajustar a oferta com base nos dados.",
            ]

            return {
                "status": "created",
                "offer_name": offer_name,
                "positioning": positioning,
                "promise": promise,
                "core_benefit": core_benefit,
                "benefits": benefits,
                "differentiator": (
                    existing_offer.get("differentiator")
                    or "orientação prática e estruturada"
                ),
                "unique_mechanism": mechanism,
                "commercial_thesis": commercial_thesis,
                "offer_stack": (
                    existing_offer.get("offer_stack")
                    or [
                        "Produto principal",
                        "Checklist de implementação",
                        "Plano de ação",
                        "Material complementar",
                    ]
                ),
                "price": float(
                    product.get("price")
                    or existing_offer.get("price")
                    or 0
                ),
                "currency": (
                    product.get("currency")
                    or existing_offer.get("currency")
                    or "BRL"
                ),
                "sales_copy": sales_copy,
                "cta": cta,
                "urgency": urgency,
                "objection_handling": objection_handling,
                "traffic_angles": traffic_angles,
                "validation_plan": validation_plan,
                "optimization": {
                    "mode": "local_commercial_optimization",
                    "based_on_real_sales": True,
                    "total_orders": total_orders,
                    "paid_orders": paid_orders,
                    "pending_orders": pending_orders,
                    "revenue": revenue,
                    "conversion_rate_percent": conversion,
                    "preserve_product": True,
                    "expand_product": False,
                },
            }

        offer_name = (
            product.get("name")
            or product.get("title")
            or "Novo Produto Digital"
        )

        promise = (
            f"Ajudar {audience} a resolver {problem} "
            f"de forma prática e estruturada."
        )

        benefits = [
            f"Aplicação prática para {problem}.",
            f"Orientação específica para {audience}.",
            "Passo a passo estruturado.",
            "Checklist de implementação.",
            "Plano de ação.",
        ]

        return {
            "status": "created",
            "offer_name": offer_name,
            "positioning": (
                f"Solução prática para {audience}, "
                f"voltada para {problem}."
            ),
            "promise": promise,
            "core_benefit": benefits[0],
            "benefits": benefits,
            "differentiator": "orientação prática e estruturada",
            "unique_mechanism": mechanism,
            "commercial_thesis": "",
            "offer_stack": [
                "Produto principal",
                "Checklist de implementação",
                "Plano de ação",
                "Material complementar",
            ],
            "price": float(product.get("price") or 0),
            "currency": product.get("currency") or "BRL",
            "sales_copy": (
                f"{offer_name}\n\n"
                f"{promise}\n\n"
                f"Desenvolvido para {audience}, "
                f"com foco em execução e resultado."
            ),
            "cta": "Quero começar agora",
            "urgency": (
                f"Comece agora e transforme {problem} "
                f"em um plano de ação."
            ),
            "objection_handling": [
                {
                    "objection": "Não tenho tempo.",
                    "response": (
                        "A solução foi organizada em etapas curtas."
                    ),
                },
                {
                    "objection": "Não sei por onde começar.",
                    "response": (
                        "O método apresenta um caminho estruturado."
                    ),
                },
                {
                    "objection": "Será que funciona para mim?",
                    "response": (
                        "A proposta é orientada ao problema específico."
                    ),
                },
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
