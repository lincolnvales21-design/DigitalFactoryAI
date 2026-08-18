from pydantic import BaseModel


class PlanStep(BaseModel):

    id: str
    agent: str
    task: str
    depends_on: list[str] = []


class Plan(BaseModel):

    objective: str
    steps: list[PlanStep]


    def to_dict(self):

        return {
            "objective": self.objective,
            "steps": [
                step.model_dump()
                for step in self.steps
            ]
        }