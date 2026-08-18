from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"



@dataclass
class WorkflowStep:

    id: str

    # Novo campo: define qual agente executa a tarefa
    agent: str

    task: str

    depends_on: list[str] = field(
        default_factory=list
    )

    status: WorkflowStatus = WorkflowStatus.PENDING

    result: Any = None

    error: str | None = None



    def to_dict(self):

        return {

            "id": self.id,

            "agent": self.agent,

            "task": self.task,

            "depends_on": self.depends_on,

            "status": self.status.value,

            "result": self.result,

            "error": self.error
        }





@dataclass
class Workflow:


    id: str

    name: str

    steps: list[WorkflowStep]

    status: WorkflowStatus = WorkflowStatus.PENDING



    def to_dict(self):

        return {

            "id": self.id,

            "name": self.name,

            "steps": [

                step.to_dict()

                for step in self.steps

            ],

            "status": self.status.value

        }