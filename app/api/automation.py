from fastapi import APIRouter

from app.agents.manager import manager
from app.schemas.automation import WorkflowRequest
from app.automation.models import Workflow, WorkflowStep

import uuid


router = APIRouter(
    prefix="/automation",
    tags=["Automation"]
)


@router.post("/run")
async def run_automation(data: WorkflowRequest):

    automation_agent = None

    for agent in manager.agents:

        if "orchestration" in agent.capabilities:
            automation_agent = agent
            break


    if automation_agent is None:

        return {
            "error": "AutomationAgent não encontrado"
        }


    workflow = Workflow(
        id=str(uuid.uuid4()),
        name=data.name,
        steps=[
            WorkflowStep(
                id=step.id,
                agent=step.agent,
                task=step.task,
                depends_on=step.depends_on
            )
            for step in data.steps
        ]
    )


    result = await automation_agent.run_workflow(
        workflow
    )


    return result.to_dict()