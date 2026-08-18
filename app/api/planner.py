from fastapi import APIRouter
from pydantic import BaseModel

from app.planner.planner import planner
from app.planner.executor import executor


router = APIRouter(
    prefix="/planner",
    tags=["Planner"]
)


class PlannerRequest(BaseModel):

    objective: str



@router.post("/create-plan")
async def create_plan(data: PlannerRequest):

    plan = await planner.create_plan(
        data.objective
    )

    return plan.to_dict()



@router.post("/execute-plan")
async def execute_plan(data: PlannerRequest):

    plan = await planner.create_plan(
        data.objective
    )

    result = await executor.execute(
        plan
    )

    if hasattr(result, "to_dict"):
        return result.to_dict()

    return result