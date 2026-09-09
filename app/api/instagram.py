import os
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(
    prefix="/instagram",
    tags=["Instagram"],
)

GRAPH_URL = "https://graph.instagram.com"


def get_token():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_ACCESS_TOKEN não configurado",
        )
    return token


@router.get("/status")
async def instagram_status():
    token = get_token()

    response = requests.get(
        f"{GRAPH_URL}/me",
        params={
            "fields": "id,username",
            "access_token": token,
        },
        timeout=20,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    data = response.json()

    return {
        "status": "connected",
        "platform": "instagram",
        "id": data.get("id"),
        "username": data.get("username"),
    }


@router.get("/media")
async def instagram_media():
    token = get_token()

    response = requests.get(
        f"{GRAPH_URL}/me/media",
        params={
            "fields": "id,caption,media_type,media_url,timestamp",
            "limit": 10,
            "access_token": token,
        },
        timeout=20,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()


class PreparePostRequest(BaseModel):
    caption: str


@router.post("/prepare")
async def prepare_post(request: PreparePostRequest):
    return {
        "status": "prepared",
        "platform": "instagram",
        "username": "lincolnvales21",
        "caption": request.caption,
        "published": False,
        "message": "Publicação preparada. Nenhum conteúdo foi publicado.",
    }



@router.get("/media/{product_id}")
async def instagram_product_image(product_id: int):
    from PIL import Image

    png_path = Path(
        f"generated_products/design/product_{product_id}_cover.png"
    )

    jpg_path = Path(
        f"generated_products/design/product_{product_id}_instagram.jpg"
    )

    if not png_path.exists() and not jpg_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Imagem do produto não encontrada",
        )

    if png_path.exists():
        try:
            image = Image.open(png_path).convert("RGB")
            image.save(
                jpg_path,
                "JPEG",
                quality=90,
                optimize=True,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao preparar imagem: {exc}",
            )

    return FileResponse(
        jpg_path,
        media_type="image/jpeg",
    )


@router.get("/test-image")
async def instagram_test_image():
    image_path = Path("generated_products/design/instagram_test.jpg")

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Imagem de teste não encontrada",
        )

    return FileResponse(
        image_path,
        media_type="image/jpeg",
    )


class CreatePostRequest(BaseModel):
    caption: str
    image_url: str


@router.post("/create")
async def create_instagram_post(request: CreatePostRequest):
    token = get_token()

    response = requests.post(
        f"{GRAPH_URL}/me/media",
        params={
            "image_url": request.image_url,
            "caption": request.caption,
            "access_token": token,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return {
        "status": "created",
        "platform": "instagram",
        "container": response.json(),
    }


@router.post("/publish/{creation_id}")
async def publish_instagram_post(creation_id: str):
    token = get_token()

    response = requests.post(
        f"{GRAPH_URL}/me/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": token,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return {
        "status": "published",
        "platform": "instagram",
        "creation_id": creation_id,
        "publication": response.json(),
    }
