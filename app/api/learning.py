
from fastapi import APIRouter
from app.business.learning_engine import learning_engine

router = APIRouter(
    prefix="/learning",
    tags=["Learning"]
)


@router.get("/metrics")
async def learning_metrics():
    return learning_engine.metrics()


@router.get("/products")
async def learning_products():
    return learning_engine.product_performance()


@router.post("/learn")
async def learning_run():
    return learning_engine.learn()


@router.get("/status")
async def learning_status():
    return learning_engine.status()
