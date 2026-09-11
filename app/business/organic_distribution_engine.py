from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

from app.business.acquisition_tracker import acquisition_tracker
from app.business.publication_tracker import publication_tracker


class OrganicDistributionEngine:

    CONTENT_TYPES = (
        "problem",
        "benefit",
        "education",
        "transformation",
        "offer",
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

        cta = (
            offer.get("cta")
            or "Quero começar agora"
        )

        problem = (
            product.get("problem")
            or "Muitas pessoas sabem o que precisam fazer, mas não sabem por onde começar."
        )

        base = {
            "product_id": product_id,
            "product_name": product_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        variations = []

        variations.append({
            **base,
            "content_type": "problem",
            "title": f"Você também enfrenta isso?",
            "caption": (
                f"{problem}\n\n"
                f"{promise}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        benefit_text = (
            benefits[0]
            if benefits
            else promise
        )

        variations.append({
            **base,
            "content_type": "benefit",
            "title": f"O que você pode conquistar",
            "caption": (
                f"{product_name}\n\n"
                f"{promise}\n\n"
                f"Um dos principais benefícios: {benefit_text}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        education_text = (
            benefits[1]
            if len(benefits) > 1
            else benefit_text
        )

        variations.append({
            **base,
            "content_type": "education",
            "title": "Uma dica prática",
            "caption": (
                f"Uma coisa importante sobre esse problema:\n\n"
                f"{education_text}\n\n"
                f"É justamente esse tipo de aplicação prática que "
                f"o {product_name} ajuda a organizar.\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
            ),
        })

        transformation_text = (
            "sair da dúvida para um caminho mais claro e prático"
        )

        variations.append({
            **base,
            "content_type": "transformation",
            "title": "Do problema para a ação",
            "caption": (
                f"{product_name}\n\n"
                f"A proposta é simples: {transformation_text}.\n\n"
                f"{promise}\n\n"
                f"{cta}\n\n"
                "#DigitalFactoryAI #NegociosDigitais #Empreendedorismo"
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
