
from fastapi import APIRouter

from app.business.optimization_engine import (
    optimization_engine
)


router = APIRouter(
    prefix="/optimization",
    tags=["Optimization"]
)


@router.get("/analysis")
async def optimization_analysis():
    return optimization_engine.analyze_all()


@router.get("/next")
async def optimization_next():
    return optimization_engine.next_move()


@router.post("/run")
async def optimization_run():
    return optimization_engine.optimize()


@router.get("/history")
async def optimization_history():
    return optimization_engine.history()
