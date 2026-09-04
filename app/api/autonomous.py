
from fastapi import APIRouter

from app.business.autonomous_decision_loop import (
    autonomous_decision_loop
)


router = APIRouter(
    prefix="/autonomous",
    tags=["Autonomous Decision Loop"]
)


@router.get("/decision")
async def autonomous_decision():
    return autonomous_decision_loop.decide()


@router.get("/next-cycle")
async def autonomous_next_cycle():
    return autonomous_decision_loop.build_cycle_objective()


@router.post("/prepare")
async def autonomous_prepare():
    return await autonomous_decision_loop.execute_next_cycle()


@router.get("/decision-history")
async def autonomous_decision_history():
    return autonomous_decision_loop.history()
