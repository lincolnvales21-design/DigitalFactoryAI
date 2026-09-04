
from fastapi import APIRouter
from app.business.supervisor import autonomous_supervisor

router = APIRouter(
    prefix="/supervisor",
    tags=["Supervisor"]
)


@router.get("/plan")
async def supervisor_plan():
    return autonomous_supervisor.plan()


@router.post("/run")
async def supervisor_run():
    return await autonomous_supervisor.run_cycle()


@router.get("/status")
async def supervisor_status():
    return autonomous_supervisor.status()
