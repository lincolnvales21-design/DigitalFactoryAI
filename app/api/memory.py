from fastapi import APIRouter

from app.memory.agent_memory import memory


router = APIRouter(
    prefix="/memory",
    tags=["Memory"]
)


@router.get("/history")
def history():

    return memory.history()