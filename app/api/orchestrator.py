
from fastapi import APIRouter

from app.business.autonomous_action_orchestrator import (
    autonomous_action_orchestrator
)


router = APIRouter(
    prefix="/orchestrator",
    tags=["Autonomous Orchestrator"]
)


@router.get("/plan")
async def orchestrator_plan():
    return autonomous_action_orchestrator.get_decision()


@router.post("/execute")
async def orchestrator_execute():
    return await autonomous_action_orchestrator.execute_decision()


@router.get("/history")
async def orchestrator_history():
    return autonomous_action_orchestrator.history()
