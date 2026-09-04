
from fastapi import APIRouter

from app.business.autonomous_scheduler_bridge import (
    autonomous_scheduler_bridge
)


router = APIRouter(
    prefix="/autonomous-runner",
    tags=["Autonomous Runner"]
)


@router.post("/start")
async def start_runner(
    interval: int = 3600,
    max_cycles: int = 1
):
    return autonomous_scheduler_bridge.start(
        interval=interval,
        max_cycles=max_cycles
    )


@router.post("/pause")
async def pause_runner():
    return autonomous_scheduler_bridge.pause()


@router.post("/resume")
async def resume_runner():
    return autonomous_scheduler_bridge.resume()


@router.post("/stop")
async def stop_runner():
    return autonomous_scheduler_bridge.stop()


@router.post("/run-once")
async def run_once():
    return await autonomous_scheduler_bridge.run_once()


@router.get("/status")
async def runner_status():
    return autonomous_scheduler_bridge.status()
