
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.business.scheduler import autonomous_scheduler


router = APIRouter(
    prefix="/scheduler",
    tags=["Autonomous Scheduler"]
)


class SchedulerStartRequest(BaseModel):
    max_cycles: int = Field(default=1, ge=1, le=100)
    interval_seconds: int = Field(default=3600, ge=10)


@router.post("/start")
async def scheduler_start(
    data: SchedulerStartRequest
):
    return await autonomous_scheduler.start(
        max_cycles=data.max_cycles,
        interval_seconds=data.interval_seconds,
    )


@router.post("/pause")
async def scheduler_pause():
    return autonomous_scheduler.pause()


@router.post("/resume")
async def scheduler_resume():
    return autonomous_scheduler.resume()


@router.post("/stop")
async def scheduler_stop():
    return autonomous_scheduler.stop()


@router.get("/status")
async def scheduler_status():
    return autonomous_scheduler.status()


@router.get("/history")
async def scheduler_history():
    return autonomous_scheduler.history()
