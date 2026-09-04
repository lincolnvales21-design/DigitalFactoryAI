
from fastapi import APIRouter

from app.business.autonomous_cycle_gate import (
    autonomous_cycle_gate
)


router = APIRouter(
    prefix="/cycle-gate",
    tags=["Autonomous Cycle Gate"]
)


@router.get("/decision")
async def cycle_gate_decision():
    return autonomous_cycle_gate.analyze()


@router.get("/history")
async def cycle_gate_history():
    return autonomous_cycle_gate.history()
