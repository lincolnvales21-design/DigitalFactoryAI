
import json
import re
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

        # Para produtos existentes, a identidade comercial atual
        # do produto nunca deve ser herdada de uma oferta antiga.
        # A oferta anterior pode estar contaminada por pesquisa genérica.
        audience = (
            product.get("target_audience")
            or product.get("audience")
            or "pessoas que buscam uma solução prática"
        )

        # =====================================================
        # CONTEXTO COMERCIAL LIMPO
        # =====================================================
        # Nunca usar a description longa como problema principal.
        # O problema deve vir do Radar/ProductAgent quando disponível.
        # Isso evita que posicionamento, ângulo, diferencial e formato
        # sejam incorporados acidentalmente à copy como se fossem o
        # problema do cliente.

        description_context = (
            product.get("description")
            if isinstance(product.get("description"), str)
            else ""
        )

        description_lower = description_context.lower()

        product_problem_from_description = None
        product_audience_from_description = None

        if (
            "automatizar tarefas administrativas" in description_lower
            or "tarefas administrativas repetitivas" in description_lower
        ):
            product_problem_from_description = (
                "tarefas administrativas repetitivas"
            )

        if "profissionais autônomos" in description_lower:
            product_audience_from_description = "profissionais autônomos"

        if (
            "tarefas administrativas" in description_lower
            or "tarefas repetitivas" in description_lower
            or "automatizar tarefas" in description_lower
        ):
            product_problem_from_description = (
                "profissionais autônomos perdem tempo com tarefas administrativas repetitivas"
            )

        # Produto atual e descrição são soberanos.
        # Não reutilizar problema de oferta anterior ou pesquisa global
        # quando o próprio produto já permite identificar o contexto.
        clean_problem = (
            product.get("problem")
            or product_problem_from_description
            or novelty.get("problem")
            or (
                research.get("problem")
                if not optimize_existing
                else None
            )
        )

        if product_problem_from_description:
            clean_problem = product_problem_from_description

        if isinstance(clean_problem, str):
            clean_problem = clean_problem.strip()

        # Normalização específica para produtos de automação administrativa.
        # Evita que contexto de pesquisa genérico seja incorporado à dor.
        if (
            "automatizar tarefas administrativas" in description_lower
            or "tarefas administrativas repetitivas" in description_lower
        ):
            clean_problem = "tarefas administrativas repetitivas"

        if not clean_problem:
            clean_problem = "tarefas repetitivas e perda de tempo na rotina"

        clean_audience = (
            product.get("target_audience")
            or product.get("audience")
            or product_audience_from_description
            or novelty.get("target_audience")
            or (
                research.get("target_audience")
                if not optimize_existing
                else None
            )
        )

        if product_audience_from_description:
            clean_audience = product_audience_from_description

        if isinstance(clean_audience, str):
            clean_audience = clean_audience.strip()

        if not clean_audience:
            clean_audience = "pessoas que buscam uma solução prática"

        clean_angle = (
            product.get("product_angle")
            or research.get("product_angle")
            or novelty.get("product_angle")
            or ""
        )

        if isinstance(clean_angle, str):
            clean_angle = clean_angle.strip()

        clean_differentiation = (
            product.get("differentiation_strategy")
            or research.get("differentiation_strategy")
            or novelty.get("differentiation_strategy")
            or existing_offer.get("differentiation_strategy")
            or "orientação prática e estruturada"
        )

        if isinstance(clean_differentiation, str):
            clean_differentiation = clean_differentiation.strip()

        clean_mechanism = (
            product.get("unique_mechanism")
            or research.get("unique_mechanism")
            or novelty.get("unique_mechanism")
            or existing_offer.get("unique_mechanism")
            or "método prático e estruturado"
        )

        if isinstance(clean_mechanism, str):
            clean_mechanism = clean_mechanism.strip()

        # =====================================================
        # LINGUAGEM DE COPY AUTOMÁTICA
        # =====================================================
        # Converte problemas técnicos em frases naturais para
        # promessa, benefícios e conteúdo comercial.
        problem_for_copy = clean_problem
        solution_phrase = clean_problem

        if isinstance(clean_problem, str):
            raw_problem = clean_problem.strip().rstrip(".")
            lowered_problem = raw_problem.lower()

            if lowered_problem.startswith("automatizar "):
                core = raw_problem[len("automatizar "):].strip()

                core = re.sub(
                    r"\s+usando\s+inteligência artificial$",
                    "",
                    core,
                    flags=re.IGNORECASE,
                )
                core = re.sub(
                    r"\s+com\s+inteligência artificial$",
                    "",
                    core,
                    flags=re.IGNORECASE,
                )

                if "repetitiv" not in core.lower():
                    problem_for_copy = f"{core} repetitivas"
                else:
                    problem_for_copy = core

                solution_phrase = (
                    f"automatizar {problem_for_copy} "
                    f"com inteligência artificial"
                )
            else:
                problem_for_copy = raw_problem
                solution_phrase = raw_problem

        audience_for_copy = clean_audience

        if isinstance(audience_for_copy, str):
            audience_for_copy = audience_for_copy.strip()

            if audience_for_copy.lower() == "profissionais autônomos":
                audience_for_copy = "profissional autônomo"

        customer_problem_sentence = (
            f"Você é {audience_for_copy} e perde tempo com "
            f"{problem_for_copy}?"
        )

        # Variáveis canônicas usadas pelo restante do fallback.
        problem = clean_problem
        audience = audience_for_copy
        mechanism = clean_mechanism

        if optimize_existing and total_orders > 0:
            offer_name = (
                existing_offer.get("offer_name")
                or title
            )

            positioning = (
                f"{offer_name} apresentada de forma simples, "
                f"prática e orientada a resultado, mostrando "
                f"parte do método sem entregar o conteúdo completo."
            )

            promise = (
                f"Aprender como lidar com {problem_for_copy} "
                f"de forma mais simples, prática e organizada, "
                f"usando um método pensado para {audience}."
            )

            core_benefit = (
                f"Conhecer uma forma prática de lidar com "
                f"{problem_for_copy} e aplicar o método no dia a dia."
            )

            benefits = [
                f"Identificar quais {problem_for_copy} mais consomem tempo.",
                f"Aprender uma abordagem prática para lidar com {problem_for_copy}.",
                "Aplicar o método passo a passo.",
                "Usar exemplos e checklists para executar.",
                "Ter um plano de ação para continuar depois da amostra.",
            ]

            sales_copy = (
                f"{offer_name}\n\n"
                f"{customer_problem_sentence}\n\n"
                f"Veja uma abordagem prática para entender o que pode "
                f"ser simplificado, automatizado ou organizado na sua rotina.\n\n"
                f"Esta é apenas uma amostra do método. O conteúdo completo "
                f"aprofunda o passo a passo, apresenta exemplos, checklists "
                f"e orientações para colocar tudo em prática.\n\n"
                f"Se esta pequena parte já mostrou um caminho, imagine "
                f"ter o método completo para consultar quando precisar.\n\n"
                f"Você recebe:\n"
                f"• {benefits[0]}\n"
                f"• {benefits[1]}\n"
                f"• {benefits[2]}\n"
                f"• {benefits[3]}\n"
                f"• {benefits[4]}\n\n"
                f"Conheça o conteúdo completo e comece a aplicar."
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
                "Veja uma pequena parte agora e descubra o que "
                "você ainda pode aprender no conteúdo completo."
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
                "Você está cometendo este erro sem perceber?",
                "Um passo simples que pode mudar sua abordagem",
                "Veja uma pequena parte do método",
                "O que ninguém explica sobre este problema",
                "Antes de comprar, veja esta amostra",
                "Descubra o que existe no conteúdo completo",
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
                "problem": clean_problem,
                "target_audience": clean_audience,
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

        product_angle = clean_angle

        differentiation = clean_differentiation

        promise = (
            f"Aprender como lidar com {problem_for_copy} "
            f"de forma mais simples, prática e organizada, "
            f"usando um método pensado para {audience}."
        )

        benefits = [
            f"Identificar quais {problem_for_copy} mais consomem tempo.",
            f"Aprender uma abordagem prática para lidar com {problem_for_copy}.",
            "Aplicar o método passo a passo.",
            "Usar exemplos e checklists para executar.",
            "Ter um plano claro para continuar depois da primeira aplicação.",
        ]

        sales_copy = (
            f"{offer_name}\n\n"
            f"{customer_problem_sentence}\n\n"
            f"Veja como identificar o que pode ser simplificado "
            f"ou automatizado e transformar tarefas repetitivas "
            f"em fluxos mais simples e organizados.\n\n"
            f"Uma pequena amostra do método:\n"
            f"1. Identifique o que está se repetindo.\n"
            f"2. Separe o que pode ser simplificado ou automatizado.\n"
            f"3. Estruture o primeiro fluxo de execução.\n"
            f"4. Teste e ajuste antes de ampliar.\n\n"
            f"Isso é apenas uma amostra. O conteúdo completo aprofunda "
            f"o método, apresenta o passo a passo, exemplos, checklists "
            f"e orientações para colocar tudo em prática.\n\n"
            f"Se essa pequena parte já mostrou um caminho, imagine ter "
            f"o método completo para consultar quando precisar.\n\n"
            f"Você recebe:\n"
            f"• {benefits[0]}\n"
            f"• {benefits[1]}\n"
            f"• {benefits[2]}\n"
            f"• {benefits[3]}\n"
            f"• {benefits[4]}\n\n"
            f"Conheça o conteúdo completo e comece a aplicar."
        )

        return {
            "status": "created",
            "offer_name": offer_name,
            "positioning": (
                f"Conteúdo prático para {audience} que precisam "
                f"lidar melhor com {problem_for_copy}, usando uma abordagem "
                f"simples e orientada à aplicação."
            ),
            "promise": promise,
            "problem": clean_problem,
            "target_audience": clean_audience,
            "core_benefit": (
                f"Dar a {audience} um caminho claro para começar "
                f"a lidar com {problem_for_copy}."
            ),
            "benefits": benefits,
            "differentiator": differentiation,
            "unique_mechanism": (
                product.get("unique_mechanism")
                or research.get("unique_mechanism")
                or novelty.get("unique_mechanism")
                or mechanism
            ),
            "commercial_thesis": (
                f"Mostrar uma pequena parte do método gratuitamente "
                f"para gerar valor imediato, curiosidade e interesse "
                f"pelo conteúdo completo."
            ),
            "offer_stack": [
                "Conteúdo completo",
                "Passo a passo de aplicação",
                "Checklist de implementação",
                "Plano de ação",
                "Material complementar",
            ],
            "price": float(product.get("price") or 0),
            "currency": product.get("currency") or "BRL",
            "sales_copy": sales_copy,
            "cta": "Quero conhecer o conteúdo completo",
            "urgency": (
                "Veja a amostra, entenda o método e descubra "
                "o que você ainda pode aplicar com o conteúdo completo."
            ),
            "objection_handling": [
                {
                    "objection": "Não sei se isso é para mim.",
                    "response": (
                        f"Este conteúdo foi estruturado especificamente "
                        f"para {audience} e parte do problema: {problem}."
                    ),
                },
                {
                    "objection": "Não tenho tempo.",
                    "response": (
                        "O método foi organizado em etapas práticas "
                        "para facilitar a aplicação."
                    ),
                },
                {
                    "objection": "Não sei por onde começar.",
                    "response": (
                        "A primeira etapa é identificar o que está "
                        "causando o problema e aplicar o primeiro fluxo."
                    ),
                },
            ],
            "traffic_angles": [
                f"O erro que faz {audience} perder tempo com {problem}",
                f"Um passo simples para começar a lidar com {problem}",
                "Veja uma pequena parte do método antes de comprar",
                f"O que ninguém explica sobre {problem}",
                f"Como {audience} pode começar a simplificar esse problema",
                f"Descubra o que existe no conteúdo completo",
            ],
            "validation_plan": [
                "Publicar uma pequena amostra útil relacionada ao problema.",
                "Testar ângulos de problema, dica, curiosidade e transformação.",
                "Medir alcance, interação e cliques.",
                "Apresentar o conteúdo completo com CTA.",
                "Medir pedidos e vendas.",
                "Ajustar copy e distribuição com base nos dados reais.",
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
