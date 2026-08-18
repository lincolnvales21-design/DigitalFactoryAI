from fastapi import APIRouter
from pydantic import BaseModel

from app.security.agent_guard import agent_guard
from app.security.permissions import Role


router = APIRouter(
    prefix="/admin/agent-guard",
    tags=["Agent Guard"]
)


class GuardRequest(BaseModel):
    role: str
    action: str
    agent_name: str


@router.post("/authorize")
async def authorize(request: GuardRequest):

    try:
        role = Role(request.role)
    except ValueError:
        return {
            "allowed": False,
            "status": "denied",
            "reason": f"Role inválida: {request.role}"
        }

    return agent_guard.authorize(
        role,
        request.action,
        request.agent_name
    )