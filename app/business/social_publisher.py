import os
from pathlib import Path

import requests
import time

from app.business.publication_tracker import publication_tracker
from app.business.acquisition_tracker import acquisition_tracker
from app.business.organic_distribution_engine import organic_distribution_engine


GRAPH_URL = "https://graph.instagram.com"


class SocialPublisher:

    def __init__(self):
        self.public_url = (
            os.getenv("DIGITALFACTORY_PUBLIC_URL")
            or os.getenv("REPLIT_DEPLOYMENT_URL")
        )

    def _get_token(self):
        return os.getenv("INSTAGRAM_ACCESS_TOKEN")

    def _build_caption(self, product, offer):
        product_name = (
            offer.get("offer_name")
            or product.get("name")
            or "Novo produto digital"
        )

        promise = (
            offer.get("promise")
            or "Conhecimento prático para transformar ideias em ações."
        )

        benefits = offer.get("benefits") or []

        if not isinstance(benefits, list):
            benefits = [str(benefits)]

        lines = [
            product_name,
            "",
            promise,
        ]

        if benefits:
            lines.extend([
                "",
                "Você vai aprender:",
            ])

            for benefit in benefits[:5]:
                lines.append(f"• {benefit}")

        cta = offer.get("cta")

        if cta:
            lines.extend([
                "",
                str(cta),
            ])

        lines.extend([
            "",
            "#DigitalFactoryAI",
            "#NegociosDigitais",
            "#Empreendedorismo",
        ])

        return "\n".join(lines)[:2200]

    def _image_path(self, product_id):
        png_path = Path(
            f"generated_products/design/product_{product_id}_cover.png"
        )

        jpg_path = Path(
            f"generated_products/design/product_{product_id}_instagram.jpg"
        )

        if not png_path.exists():
            return jpg_path if jpg_path.exists() else None

        try:
            from PIL import Image

            image = Image.open(png_path).convert("RGB")

            image.save(
                jpg_path,
                "JPEG",
                quality=90,
                optimize=True,
            )

            return jpg_path

        except Exception:
            return png_path

    def image_url(self, product_id):
        if not self.public_url:
            return None

        return (
            f"{self.public_url.rstrip('/')}"
            f"/instagram/media/{int(product_id)}"
        )

    async def publish(self, product, offer, variation=None):
        product_id = (
            product.get("id")
            or product.get("product_id")
        )

        if not product_id:
            return {
                "status": "blocked",
                "reason": "Produto sem product_id.",
            }

        token = self._get_token()

        if not token:
            return {
                "status": "blocked",
                "reason": "INSTAGRAM_ACCESS_TOKEN não configurado.",
            }

        image_path = self._image_path(product_id)

        if not image_path:
            return {
                "status": "blocked",
                "product_id": int(product_id),
                "reason": "Imagem comercial do produto não encontrada.",
            }

        image_url = self.image_url(product_id)

        if not image_url:
            return {
                "status": "blocked",
                "product_id": int(product_id),
                "reason": "DIGITALFACTORY_PUBLIC_URL não configurada.",
            }

        if variation:
            tracking_url = variation.get("tracking_url")
            medium = variation.get("medium") or "organic_social"
        else:
            acquisition = acquisition_tracker.generate_link(
                product_id=int(product_id),
                channel="instagram",
                source="instagram",
                campaign=f"produto-{int(product_id)}",
                medium="organic_social",
                base_url=self.public_url,
            )

            tracking_url = acquisition.get("tracking_url")
            medium = "organic_social"

        if not tracking_url:
            return {
                "status": "blocked",
                "product_id": int(product_id),
                "reason": "Não foi possível gerar URL de aquisição.",
            }

        caption = (
            variation.get("caption")
            if variation
            else self._build_caption(
                product,
                offer,
            )
        )

        if not caption:
            return {
                "status": "blocked",
                "product_id": int(product_id),
                "reason": "Conteúdo orgânico vazio.",
            }

        try:
            create_response = requests.post(
                f"{GRAPH_URL}/me/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": token,
                },
                timeout=30,
            )

            if create_response.status_code != 200:
                return {
                    "status": "failed",
                    "product_id": int(product_id),
                    "stage": "create",
                    "http_status": create_response.status_code,
                    "error": create_response.text,
                }

            container = create_response.json()
            creation_id = container.get("id")

            if not creation_id:
                return {
                    "status": "failed",
                    "product_id": int(product_id),
                    "stage": "create",
                    "reason": "Instagram não retornou creation_id.",
                    "container": container,
                }

            # O Instagram pode precisar de alguns segundos para processar
            # o container antes de aceitar media_publish.
            # Fazemos polling controlado para evitar o erro 9007/2207027.
            container_ready = False
            last_status = None

            for attempt in range(10):
                status_response = requests.get(
                    f"{GRAPH_URL}/{creation_id}",
                    params={
                        "fields": "status_code",
                        "access_token": token,
                    },
                    timeout=30,
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    last_status = status_data.get("status_code")

                    if last_status == "FINISHED":
                        container_ready = True
                        break

                    if last_status in {"ERROR", "EXPIRED"}:
                        return {
                            "status": "failed",
                            "product_id": int(product_id),
                            "stage": "container",
                            "creation_id": creation_id,
                            "container_status": last_status,
                            "error": status_response.text,
                        }

                time.sleep(3)

            if not container_ready:
                return {
                    "status": "failed",
                    "product_id": int(product_id),
                    "stage": "container",
                    "creation_id": creation_id,
                    "container_status": last_status,
                    "reason": "Container do Instagram não ficou pronto dentro do tempo limite.",
                }

            publish_response = requests.post(
                f"{GRAPH_URL}/me/media_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": token,
                },
                timeout=30,
            )

            if publish_response.status_code != 200:
                return {
                    "status": "failed",
                    "product_id": int(product_id),
                    "stage": "publish",
                    "creation_id": creation_id,
                    "http_status": publish_response.status_code,
                    "error": publish_response.text,
                }

            publication = publish_response.json()
            publication_id = publication.get("id")

            tracker = publication_tracker.create_publication(
                product_id=int(product_id),
                channel="instagram",
                title=product.get("name"),
                content=caption,
                tracking_url=tracking_url,
                source="instagram",
                campaign="autonomous_factory",
                medium=medium,
                status="published",
                external_id=(
                    str(publication_id)
                    if publication_id
                    else None
                ),
            )

            publication_tracker.log_activity(
                activity_type="instagram_publication",
                product_id=int(product_id),
                title="Publicação automática no Instagram",
                description=(
                    "Produto publicado automaticamente "
                    "após aprovação do ProductFactory."
                ),
                status="completed",
                metadata={
                    "creation_id": creation_id,
                    "publication_id": publication_id,
                    "image_url": image_url,
                    "channel": "instagram",
                    "content_type": variation.get("content_type") if variation else "default",
                    "title": variation.get("title") if variation else None,
                    "medium": medium,
                },
            )

            return {
                "status": "published",
                "platform": "instagram",
                "product_id": int(product_id),
                "creation_id": creation_id,
                "publication_id": publication_id,
                "image_url": image_url,
                "tracking_url": tracking_url,
                "caption": caption,
                "content_type": variation.get("content_type") if variation else "default",
                "medium": medium,
                "tracker": tracker,
            }

        except Exception as exc:
            return {
                "status": "failed",
                "product_id": int(product_id),
                "reason": str(exc),
            }


    async def sync_insights(self, publication_id, tracker_publication_id):
        """
        Sincroniza Insights reais do Instagram com o publication_tracker.
        """
        insights = await self.get_insights(publication_id)

        if insights.get("status") != "success":
            return insights

        from app.business.publication_tracker import publication_tracker

        acquisition = publication_tracker.publication_metrics(
            tracker_publication_id
        )

        publication_tracker.update_metrics(
            tracker_publication_id,
            views=insights.get("views", 0),
            clicks=acquisition.get("visits", 0),
            orders=acquisition.get("orders", 0),
            sales=acquisition.get("sales", 0),
            revenue=acquisition.get("revenue", 0),
            currency=acquisition.get("currency", "BRL"),
            reach=insights.get("reach", 0),
            likes=insights.get("likes", 0),
            comments=insights.get("comments", 0),
            saved=insights.get("saved", 0),
            shares=insights.get("shares", 0),
        )

        return {
            "status": "success",
            "publication_id": str(publication_id),
            "tracker_publication_id": tracker_publication_id,
            "instagram": insights,
            "acquisition": acquisition,
        }

    async def get_insights(self, publication_id):
        """
        Consulta os Insights reais de uma publicação do Instagram.
        Não publica nem altera o conteúdo.
        """
        token = self._get_token()

        if not token:
            return {
                "status": "blocked",
                "publication_id": str(publication_id),
                "reason": "INSTAGRAM_ACCESS_TOKEN não configurado.",
            }

        metrics = "reach,views,likes,comments,saved,shares"

        try:
            response = requests.get(
                f"{GRAPH_URL}/{publication_id}/insights",
                params={
                    "metric": metrics,
                    "access_token": token,
                },
                timeout=30,
            )

            if response.status_code != 200:
                return {
                    "status": "failed",
                    "publication_id": str(publication_id),
                    "http_status": response.status_code,
                    "error": response.text,
                }

            data = response.json().get("data", [])

            insights = {}

            for item in data:
                name = item.get("name")
                values = item.get("values") or []

                if name and values:
                    insights[name] = values[-1].get("value", 0)

            return {
                "status": "success",
                "platform": "instagram",
                "publication_id": str(publication_id),
                "reach": int(insights.get("reach", 0) or 0),
                "views": int(insights.get("views", 0) or 0),
                "likes": int(insights.get("likes", 0) or 0),
                "comments": int(insights.get("comments", 0) or 0),
                "saved": int(insights.get("saved", 0) or 0),
                "shares": int(insights.get("shares", 0) or 0),
            }

        except Exception as exc:
            return {
                "status": "failed",
                "publication_id": str(publication_id),
                "reason": str(exc),
            }


social_publisher = SocialPublisher()
