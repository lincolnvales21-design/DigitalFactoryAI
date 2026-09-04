import json
import os
from datetime import datetime, timezone

try:
    import sqlite3
    from pathlib import Path
except Exception:
    sqlite3 = None
    Path = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class OpportunityEngine:
    """
    Radar de oportunidades do DigitalFactoryAI.

    Responsabilidades:
      - gerar candidatos;
      - consultar produtos já existentes;
      - evitar repetição;
      - favorecer diversificação;
      - preparar oportunidades para o Novelty Engine.

    Não executa produtos.
    Não publica.
    Não movimenta capital.
    """

    AREAS = [
        "bem-estar",
        "educação",
        "finanças pessoais",
        "relacionamentos",
        "casamento",
        "pequenas empresas",
        "produtividade",
        "tecnologia",
        "marketing",
        "carreira",
        "empreendedorismo",
        "organização pessoal",
    ]

    FORMATS = [
        "ebook",
        "guia prático",
        "checklist",
        "planner",
        "template",
        "curso curto",
        "kit digital",
        "ferramenta digital",
        "diagnóstico",
    ]

    MARKETS = [
        "Brasil",
        "Estados Unidos",
        "mercado internacional",
    ]

    MAX_EXISTING_PRODUCTS = 100

    # --------------------------------------------------------
    # BANCO
    # --------------------------------------------------------

    def __init__(self):
        self.db_path = Path("digitalfactory.db")

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _existing_products(self):
        """
        Recupera produtos já criados.

        Usa os nomes reais da tabela:
          name
          description
          product_type
          price
          currency
          status
        """

        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
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
                ORDER BY id DESC
                LIMIT ?
            """, (self.MAX_EXISTING_PRODUCTS,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "product_type": row[3],
                    "price": row[4],
                    "currency": row[5],
                    "status": row[6],
                    "created_at": row[7],
                }
                for row in rows
            ]

        except Exception:
            return []

    # --------------------------------------------------------
    # NORMALIZAÇÃO
    # --------------------------------------------------------

    @staticmethod
    def _normalize(value):
        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .lower()
            .replace("-", " ")
            .replace("_", " ")
        )

    def _product_text(self, product):
        return self._normalize(
            " ".join(
                [
                    str(product.get("name") or ""),
                    str(product.get("description") or ""),
                    str(product.get("product_type") or ""),
                ]
            )
        )

    # --------------------------------------------------------
    # DIVERSIFICAÇÃO
    # --------------------------------------------------------

    def _diversification_profile(self, products):
        """
        Cria um perfil simples do que a fábrica já explorou.
        """

        formats = {}
        areas = {}

        for product in products:

            product_type = self._normalize(
                product.get("product_type")
            )

            if product_type:
                formats[product_type] = (
                    formats.get(product_type, 0) + 1
                )

            text = self._product_text(product)

            for area in self.AREAS:
                if self._normalize(area) in text:
                    areas[area] = areas.get(area, 0) + 1

        return {
            "formats_used": formats,
            "areas_explored": areas,
            "total_products": len(products),
        }

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    def _fallback_candidates(self):
        """
        Candidatos determinísticos.

        A lista usa combinações diferentes das anteriores
        para aumentar a diversidade da fábrica.
        """

        combinations = [
            (
                "pequenas empresas",
                "reduzir erros de atendimento e padronizar respostas comerciais",
                "pequenos negócios com atendimento manual",
                "template",
                "Brasil",
            ),
            (
                "finanças pessoais",
                "criar um sistema simples para organizar decisões financeiras mensais",
                "adultos com renda variável",
                "diagnóstico",
                "Brasil",
            ),
            (
                "bem-estar",
                "montar uma rotina sustentável para pessoas com pouco tempo",
                "profissionais com rotina intensa",
                "planner",
                "Estados Unidos",
            ),
            (
                "tecnologia",
                "automatizar tarefas administrativas usando inteligência artificial",
                "profissionais autônomos",
                "curso curto",
                "mercado internacional",
            ),
            (
                "relacionamentos",
                "organizar conversas importantes e decisões da vida a dois",
                "casais em fase de planejamento familiar",
                "kit digital",
                "Brasil",
            ),
            (
                "carreira",
                "estruturar uma transição profissional com análise de competências",
                "profissionais em mudança de carreira",
                "checklist",
                "Estados Unidos",
            ),
            (
                "marketing",
                "transformar conhecimento profissional em um sistema de conteúdo comercial",
                "consultores e especialistas",
                "ferramenta digital",
                "mercado internacional",
            ),
            (
                "educação",
                "criar um sistema de estudo adaptado à disponibilidade real do aluno",
                "adultos que estudam e trabalham",
                "planner",
                "Brasil",
            ),
            (
                "empreendedorismo",
                "avaliar rapidamente se uma ideia de negócio merece ser testada",
                "empreendedores iniciantes",
                "diagnóstico",
                "mercado internacional",
            ),
            (
                "organização pessoal",
                "reduzir decisões repetitivas e estruturar uma semana mais previsível",
                "pessoas com muitas responsabilidades",
                "template",
                "Estados Unidos",
            ),
        ]

        candidates = []

        for area, problem, audience, fmt, market in combinations:

            candidates.append({
                "area": area,
                "problem": problem,
                "target_audience": audience,
                "recommended_format": fmt,
                "market": market,
                "commercial_thesis": (
                    f"Pessoas do público '{audience}' podem pagar "
                    f"por uma solução prática para '{problem}'."
                ),
                "differentiation_angle": (
                    "Foco em aplicação prática, especificidade "
                    "do problema e implementação rápida."
                ),
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            })

        return candidates

    # --------------------------------------------------------
    # IA EXTERNA
    # --------------------------------------------------------

    async def discover(self):
        candidates = self._fallback_candidates()

        existing_products = self._existing_products()

        profile = self._diversification_profile(
            existing_products
        )

        api_key = os.getenv("OPENAI_API_KEY")

        if OpenAI and api_key:
            try:
                client = OpenAI(api_key=api_key)

                existing_summary = [
                    {
                        "name": product["name"],
                        "description": product["description"],
                        "product_type": product["product_type"],
                        "status": product["status"],
                    }
                    for product in existing_products
                ]

                prompt = f"""
Você é o Opportunity Radar do DigitalFactoryAI.

O sistema já possui produtos existentes.

Produtos existentes:
{json.dumps(existing_summary, ensure_ascii=False)}

Perfil de diversificação:
{json.dumps(profile, ensure_ascii=False)}

Gere 10 novas oportunidades comerciais.

Cada oportunidade deve ter:
- area
- problem
- target_audience
- recommended_format
- market
- commercial_thesis
- differentiation_angle

REGRAS IMPORTANTES:

1. Não copie produtos existentes.
2. Não repita o mesmo problema com palavras diferentes.
3. Não fique preso ao formato ebook.
4. Explore áreas diferentes.
5. Explore Brasil, Estados Unidos e mercado internacional.
6. Priorize problemas específicos e monetizáveis.
7. Procure públicos diferentes.
8. A oportunidade deve poder gerar um produto real.
9. Evite ideias genéricas.
10. Busque uma combinação nova de problema + público + formato + mercado.

Retorne SOMENTE JSON em formato de lista.
"""

                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um radar comercial "
                                "especializado em descoberta "
                                "e diversificação de produtos."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.9,
                )

                text = (
                    response
                    .choices[0]
                    .message
                    .content
                    .strip()
                )

                generated = json.loads(text)

                if isinstance(generated, list) and generated:
                    candidates = generated

            except Exception:
                # Fallback determinístico permanece ativo.
                pass

        return candidates

    # --------------------------------------------------------
    # PONTUAÇÃO
    # --------------------------------------------------------

    def _score_candidate(
        self,
        candidate,
        existing_products,
    ):
        score = 0

        text = json.dumps(
            candidate,
            ensure_ascii=False,
        ).lower()

        # Qualidade básica
        if candidate.get("problem"):
            score += 20

        if candidate.get("target_audience"):
            score += 20

        if candidate.get("commercial_thesis"):
            score += 20

        if candidate.get("differentiation_angle"):
            score += 20

        if candidate.get("recommended_format"):
            score += 10

        if len(text) > 150:
            score += 10

        # ----------------------------------------------------
        # DIVERSIFICAÇÃO
        # ----------------------------------------------------

        candidate_format = self._normalize(
            candidate.get("recommended_format")
        )

        existing_format_count = 0

        for product in existing_products:
            if (
                self._normalize(
                    product.get("product_type")
                )
                == candidate_format
            ):
                existing_format_count += 1

        # Quanto mais usado o formato, maior a penalização.
        score -= min(
            30,
            existing_format_count * 5,
        )

        # ----------------------------------------------------
        # REPETIÇÃO TEXTUAL
        # ----------------------------------------------------

        candidate_text = self._normalize(
            " ".join(
                [
                    str(candidate.get("problem") or ""),
                    str(candidate.get("target_audience") or ""),
                    str(candidate.get("area") or ""),
                ]
            )
        )

        repeated_similarity = 0

        for product in existing_products:
            existing_text = self._product_text(product)

            if not existing_text:
                continue

            candidate_words = set(
                candidate_text.split()
            )

            existing_words = set(
                existing_text.split()
            )

            if not candidate_words:
                continue

            overlap = len(
                candidate_words & existing_words
            ) / len(candidate_words)

            if overlap >= 0.60:
                repeated_similarity += 1

        score -= min(
            40,
            repeated_similarity * 10,
        )

        return max(0, score)

    # --------------------------------------------------------
    # SELEÇÃO
    # --------------------------------------------------------

    async def select(self):
        candidates = await self.discover()

        if not candidates:
            raise RuntimeError(
                "Opportunity Engine não encontrou oportunidades."
            )

        existing_products = self._existing_products()

        scored = []

        for candidate in candidates:

            candidate = dict(candidate)

            candidate["opportunity_score"] = (
                self._score_candidate(
                    candidate,
                    existing_products,
                )
            )

            candidate["diversification"] = {
                "existing_products_considered": len(
                    existing_products
                ),
                "format": candidate.get(
                    "recommended_format"
                ),
                "area": candidate.get("area"),
                "market": candidate.get("market"),
            }

            scored.append(candidate)

        scored.sort(
            key=lambda item: (
                item.get("opportunity_score", 0),
                item.get("diversification", {}).get(
                    "market",
                    "",
                ),
            ),
            reverse=True,
        )

        selected = scored[0]

        return {
            "status": "selected",
            "selected": selected,
            "candidates": scored,
            "diversification_profile": (
                self._diversification_profile(
                    existing_products
                )
            ),
        }


opportunity_engine = OpportunityEngine()
