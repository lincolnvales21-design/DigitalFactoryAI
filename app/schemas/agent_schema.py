from pydantic import BaseModel


class AgentTaskRequest(BaseModel):
    agent: str
    task: str