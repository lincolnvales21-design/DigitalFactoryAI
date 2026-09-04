
from fastapi import APIRouter
from pydantic import BaseModel

from app.business.action_execution_engine import (
    action_execution_engine
)


router = APIRouter(
    prefix="/actions",
    tags=["Action Execution"]
)


class ActionRequest(BaseModel):
    action: str
    product_id: int | None = None
    estimated_cost: float = 0.0


@router.get("/capital-policy")
async def capital_policy():
    return action_execution_engine.capital_policy()


@router.post("/authorize-spend")
async def authorize_spend(amount: float):
    return action_execution_engine.authorize_spend(
        amount
    )


@router.post("/execute")
async def execute_action(request: ActionRequest):
    return await action_execution_engine.execute(
        action=request.action,
        product_id=request.product_id,
        estimated_cost=request.estimated_cost,
    )


@router.get("/history")
async def action_history():
    return action_execution_engine.history()
