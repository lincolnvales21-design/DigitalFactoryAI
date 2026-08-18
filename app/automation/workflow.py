from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    id: str
    task: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    name: str
    steps: list[WorkflowStep]