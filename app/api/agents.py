from fastapi import APIRouter

from app.agents.registry import registry


router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.get("/")
def list_agents():

    return [
        agent.get_info()
        for agent in registry.list_agents()
    ]


@router.get("/capabilities")
def list_capabilities():

    return registry.list_capabilities()