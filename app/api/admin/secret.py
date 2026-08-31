from fastapi import APIRouter

from app.security.secret_manager import secret_manager


router = APIRouter(
    prefix="/admin/security",
    tags=["Security"]
)


@router.post("/rotate-secret")
async def rotate_secret():

    return secret_manager.rotate()