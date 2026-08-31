from pydantic import BaseModel, Field


class WorkflowStepRequest(BaseModel):

    id: str

    agent: str

    task: str

    depends_on: list[str] = Field(
        default_factory=list
    )


class WorkflowRequest(BaseModel):

    name: str

    steps: list[WorkflowStepRequest]