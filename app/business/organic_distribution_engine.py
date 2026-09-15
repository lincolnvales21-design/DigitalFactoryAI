from datetime import datetime, timezone

from app.business.acquisition_tracker import acquisition_tracker
from app.business.publication_tracker import publication_tracker


class OrganicDistributionEngine:

    CONTENT_TYPES = (
        "problem",
        "benefit",
        "education",
        "transformation",
        "offer",
        "common_mistake",
        "checklist",
        "question",
        "alert",
        "curiosity",
    )

    def build_variations(self, product, offer):
        product_id = int(
            product.get("id")
            or product.get("product_id")
        )

        product_name = (
            offer.get("offer_name")
            or product.get("name")
            or "Novo produto digital"
        )

        promise = (
            offer.get("promise")
            or "Uma solução prática para transformar conhecimento em ação."
        )

        benefits = offer.get("benefits") or []

        if not isinstance(benefits, list):
            benefits = [str(benefits)]

        benefits = [
            str(item).strip()
            for item in benefits
            if str(item).strip()
        ][:5]

        cta = offer.get("cta") or "Quero conhecer a solução"

        problem = (
            offer.get("problem")
            or product.get("problem")
            or "um problema específico"
        )

        audience = (
            offer.get("target_audience")
            or product.get("target_audience")
            or "pessoas que enfrentam esse problema"
        )

        problem = str(problem).strip().rstrip(".")
        audience = str(audience).strip().rstrip(".")

        problem_lower = problem.lower()

        base = {
            "product_id": product_id,
            "product_name": product_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        benefit_text = benefits[0] if benefits else promise
        education_text = (
            benefits[1]
            if len(benefits) > 1
            else benefit_text
        )

        checklist_text = (
            "\n".join(
                f"☐ {item}"
                for item in benefits[:3]
            )
            or (
                "☐ Entenda o problema\n"
                "☐ Escolha uma ação prática\n"
                "☐ Teste e ajuste"
            )
        )

        variations = []

        variations.append({
            **base,
            "content_type": "problem",
            "title": "Você também enfrenta isso?",
            "caption": (
                f"{problem}.\n\n"
                f"Para {audience}, entender esse problema "
                f"é o primeiro passo para encontrar uma solução prática.\n\n"
                f"{promise}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        if problem_lower.startswith(("avaliar ", "criar ", "organizar ", "reduzir ")):
            benefit_open = (
                f"Quando você entende melhor o que precisa fazer, "
                f"fica mais fácil agir com clareza.\n\n"
            )
        else:
            benefit_open = (
                f"Quando você entende melhor {problem_lower}, "
                f"fica mais fácil agir com clareza.\n\n"
            )

        variations.append({
            **base,
            "content_type": "benefit",
            "title": "O que pode mudar",
            "caption": (
                benefit_open
                + f"{benefit_text}\n\n"
                + f"{promise}\n\n"
                + f"{cta}\n\n"
                + "#DigitalFactoryAI #IA #NegociosDigitais"
            ),
        })

        variations.append({
            **base,
            "content_type": "education",
            "title": "Uma dica prática",
            "caption": (
                f"Uma coisa importante sobre {problem_lower}:\n\n"
                f"{education_text}\n\n"
                f"Comece por uma pequena ação e observe o que muda.\n\n"
                "#DigitalFactoryAI #Aprendizado #Tecnologia"
            ),
        })

        if problem_lower.startswith(
            ("avaliar ", "criar ", "organizar ", "reduzir ")
        ):
            transformation_open = (
                f"Você não precisa tentar {problem_lower} de uma vez."
            )
            mistake_open = (
                f"Um erro comum ao tentar {problem_lower} "
                f"é tentar resolver tudo ao mesmo tempo."
            )
            checklist_open = (
                f"Antes de {problem_lower}, confira:"
            )
            question_open = (
                f"Qual é hoje a maior dificuldade que você encontra "
                f"ao tentar {problem_lower}?"
            )
            curiosity_open = (
                f"Muitas vezes, o problema começa antes da ação: "
                f"quando não fica claro como {problem_lower}."
            )
        else:
            transformation_open = (
                f"Você não precisa resolver {problem_lower} de uma vez."
            )
            mistake_open = (
                f"Um erro comum ao lidar com {problem_lower} "
                f"é tentar resolver tudo ao mesmo tempo."
            )
            checklist_open = (
                f"Antes de agir sobre {problem_lower}, confira:"
            )
            question_open = (
                f"Qual é hoje a maior dificuldade relacionada a "
                f"{problem_lower}?"
            )
            curiosity_open = (
                f"Muitas vezes, o problema começa antes da ação: "
                f"quando não fica claro como lidar com {problem_lower}."
            )

        variations.append({
            **base,
            "content_type": "transformation",
            "title": "Do problema para a ação",
            "caption": (
                f"{transformation_open}\n\n"
                "Comece entendendo a situação, escolha uma prioridade "
                "e aplique o próximo passo do método.\n\n"
                f"{promise}\n\n"
                "#DigitalFactoryAI #Estratégia #Empreendedorismo"
            ),
        })

        variations.append({
            **base,
            "content_type": "offer",
            "title": product_name,
            "caption": (
                f"{product_name}\n\n"
                f"{promise}\n\n"
                + (
                    "\n".join(
                        f"• {item}"
                        for item in benefits[:3]
                    )
                    if benefits
                    else ""
                )
                + f"\n\n{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        variations.append({
            **base,
            "content_type": "common_mistake",
            "title": "Um erro comum",
            "caption": (
                f"{mistake_open}\n\n"
                "Escolha uma prioridade, aplique uma mudança "
                "e observe o resultado antes de avançar.\n\n"
                f"{promise}\n\n"
                "#DigitalFactoryAI #Estratégia #Produtividade"
            ),
        })

        variations.append({
            **base,
            "content_type": "checklist",
            "title": "Checklist rápido",
            "caption": (
                f"{checklist_open}\n\n"
                f"{checklist_text}\n\n"
                "Pequenas decisões bem estruturadas ajudam a avançar.\n\n"
                "#DigitalFactoryAI #Checklist #NegociosDigitais"
            ),
        })

        variations.append({
            **base,
            "content_type": "question",
            "title": "Uma pergunta para você",
            "caption": (
                f"{question_open}\n\n"
                "Identificar isso pode mostrar qual deve ser "
                "o próximo passo.\n\n"
                "Conte nos comentários.\n\n"
                "#DigitalFactoryAI #Reflexão #Empreendedorismo"
            ),
        })

        variations.append({
            **base,
            "content_type": "alert",
            "title": "Fique atento",
            "caption": (
                f"Se {problem_lower} está impedindo você de avançar, "
                "vale revisar como essa decisão está sendo tomada.\n\n"
                f"{promise}\n\n"
                "#DigitalFactoryAI #Estratégia #Tecnologia"
            ),
        })

        variations.append({
            **base,
            "content_type": "curiosity",
            "title": "Já reparou nisso?",
            "caption": (
                f"{curiosity_open}\n\n"
                f"{promise}\n\n"
                "#DigitalFactoryAI #Curiosidade #NegociosDigitais"
            ),
        })

        return variations

    def next_variation(self, product_id, offer, product=None):
        product = product or {"id": product_id}

        variations = self.build_variations(
            product=product,
            offer=offer,
        )

        existing = publication_tracker.list_publications(
            product_id=int(product_id)
        )

        instagram_publications = [
            row for row in existing
            if row.get("channel") == "instagram"
            and row.get("status") == "published"
        ]

        # Publicações rejeitadas/deletadas/suprimidas nunca
        # podem voltar para a fila em ciclos futuros.
        suppressed = []

        for row in existing:
            row_status = str(
                row.get("status") or ""
            ).strip().lower()

            if row_status in {
                "deleted",
                "rejected",
                "suppressed",
            }:
                suppressed.append(row)

        used_types = {
            row.get("medium")
            for row in instagram_publications
        }

        used_captions = {
            " ".join(
                str(row.get(key) or "").split()
            ).strip().lower()
            for row in instagram_publications
            for key in ("caption", "content", "text")
            if str(row.get(key) or "").strip()
        }

        suppressed_hashes = {
            publication_tracker._content_hash(
                row.get("content")
                or row.get("caption")
                or row.get("text")
            )
            for row in suppressed
            if (
                row.get("content")
                or row.get("caption")
                or row.get("text")
            )
        }

        # Primeiro: privilegia tipos ainda não utilizados.
        candidates = [
            variation
            for variation in variations
            if f"organic_social:{variation['content_type']}" not in used_types
        ]

        # Se todos os tipos já foram usados, permite um novo ciclo,
        # mas somente com texto realmente diferente do histórico.
        if not candidates:
            candidates = variations

        for variation in candidates:
            normalized_caption = " ".join(
                str(variation.get("caption") or "").split()
            ).strip().lower()

            if normalized_caption in used_captions:
                continue

            variation_hash = publication_tracker._content_hash(
                variation.get("caption")
            )

            if variation_hash in suppressed_hashes:
                continue

            if publication_tracker.is_suppressed(
                product_id=int(product_id),
                channel="instagram",
                content=variation.get("caption"),
            ):
                continue

            medium = f"organic_social:{variation['content_type']}"

            acquisition = acquisition_tracker.generate_link(
                product_id=int(product_id),
                channel="instagram",
                source="instagram",
                campaign=f"produto-{int(product_id)}",
                medium=medium,
            )

            variation["tracking_url"] = acquisition.get(
                "tracking_url"
            )
            variation["medium"] = medium

            return variation

        # Segurança: nunca devolve silenciosamente uma publicação
        # idêntica a uma já publicada.
        return None


organic_distribution_engine = OrganicDistributionEngine()
