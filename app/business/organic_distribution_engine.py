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

        cta = offer.get("cta") or "Quero começar agora"

        description = (
            product.get("description")
            if isinstance(product.get("description"), str)
            else ""
        )
        description_lower = description.lower()

        if (
            "automatizar tarefas administrativas" in description_lower
            or "tarefas administrativas repetitivas" in description_lower
        ):
            problem = (
                "Profissionais autônomos perdem tempo com tarefas "
                "administrativas repetitivas que poderiam ser simplificadas "
                "ou automatizadas."
            )
        else:
            problem = (
                product.get("problem")
                or "Muitas pessoas sabem o que precisam fazer, mas não sabem por onde começar."
            )

        base = {
            "product_id": product_id,
            "product_name": product_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        benefit_text = benefits[0] if benefits else promise
        education_text = benefits[1] if len(benefits) > 1 else benefit_text
        checklist_text = "\n".join(
            f"☐ {item}" for item in benefits[:3]
        ) or "☐ Identifique o problema\n☐ Escolha uma ação prática\n☐ Teste e ajuste"

        variations = []

        variations.append({
            **base,
            "content_type": "problem",
            "title": "Você também enfrenta isso?",
            "caption": (
                f"{problem}\n\n"
                f"{promise}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        variations.append({
            **base,
            "content_type": "benefit",
            "title": "O que pode mudar",
            "caption": (
                f"Para quem trabalha por conta própria, cada tarefa administrativa repetitiva pode consumir tempo que deveria estar sendo usado para atender clientes e fazer o negócio crescer.\n\n"
                f"{benefit_text}\n\n"
                f"{promise}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #IA #Automacao #Produtividade"
            ),
        })

        variations.append({
            **base,
            "content_type": "education",
            "title": "Uma dica prática",
            "caption": (
                f"Uma coisa importante sobre esse problema:\n\n"
                f"{education_text}\n\n"
                f"A ideia é transformar conhecimento em uma aplicação que você consiga usar no dia a dia.\n\n"
                f"#DigitalFactoryAI #Aprendizado #Tecnologia"
            ),
        })

        variations.append({
            **base,
            "content_type": "transformation",
            "title": "Do problema para a ação",
            "caption": (
                f"Não precisa começar tentando resolver tudo de uma vez.\n\n"
                f"Comece identificando uma tarefa, organize o processo e avance a partir daí.\n\n"
                f"{promise}\n\n"
                f"#DigitalFactoryAI #Produtividade #IA"
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
                f"Um erro comum é tentar automatizar todas as tarefas administrativas de uma vez.\n\n"
                f"Para quem trabalha por conta própria, isso pode gerar mais confusão do que economia de tempo.\n\n"
                f"Comece identificando uma tarefa administrativa repetitiva que consome tempo todos os dias.\n\n"
                f"Automatize uma etapa, teste o resultado e só depois avance para a próxima.\n\n"
                "#DigitalFactoryAI #IA #Automacao #Produtividade"
            ),
        })

        variations.append({
            **base,
            "content_type": "checklist",
            "title": "Checklist rápido",
            "caption": (
                f"Antes de começar, confira:\n\n"
                f"{checklist_text}\n\n"
                f"Pequenas melhorias consistentes podem transformar uma rotina.\n\n"
                "#DigitalFactoryAI #Checklist #Produtividade"
            ),
        })

        variations.append({
            **base,
            "content_type": "question",
            "title": "Uma pergunta para você",
            "caption": (
                f"Qual tarefa repetitiva mais toma seu tempo hoje?\n\n"
                f"Às vezes, encontrar a resposta para essa pergunta já mostra onde começar uma mudança.\n\n"
                f"Conta nos comentários.\n\n"
                "#DigitalFactoryAI #IA #Empreendedorismo"
            ),
        })

        variations.append({
            **base,
            "content_type": "alert",
            "title": "Fique atento",
            "caption": (
                f"Se uma tarefa é repetida todos os dias, vale parar e perguntar:\n\n"
                f"isso realmente precisa continuar sendo feito da mesma maneira?\n\n"
                f"{problem}\n\n"
                "#DigitalFactoryAI #Tecnologia #Produtividade"
            ),
        })

        variations.append({
            **base,
            "content_type": "curiosity",
            "title": "Já reparou nisso?",
            "caption": (
                f"Muitas tarefas que parecem pequenas acabam consumindo horas ao longo de uma semana.\n\n"
                f"O primeiro passo é perceber onde esse tempo está desaparecendo.\n\n"
                f"{promise}\n\n"
                "#DigitalFactoryAI #Curiosidade #IA"
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

        used_types = {
            row.get("medium")
            for row in existing
            if row.get("channel") == "instagram"
            and row.get("status") == "published"
        }

        for variation in variations:
            medium = f"organic_social:{variation['content_type']}"

            if medium not in used_types:
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

        return None


organic_distribution_engine = OrganicDistributionEngine()
