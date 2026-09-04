
from fastapi import APIRouter

from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator
)


router = APIRouter(
    prefix="/autonomous-cycle",
    tags=["Autonomous Cycle"]
)


@router.post("/run")
async def run_autonomous_cycle():
    return await autonomous_cycle_orchestrator.run_cycle()


@router.get("/status")
async def autonomous_cycle_status():
    return autonomous_cycle_orchestrator.status()


@router.get("/history")
async def autonomous_cycle_history():
    return autonomous_cycle_orchestrator.history()
