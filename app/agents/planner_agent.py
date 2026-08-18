from app.agents.base import BaseAgent
from app.automation.models import Workflow, WorkflowStep

import uuid



class PlannerAgent(BaseAgent):


    def __init__(self):

        super().__init__("PlannerAgent")

        self.add_capability("planning")
        self.add_capability("task_breakdown")
        self.add_capability("orchestration")



    async def create_plan(self, objective: str):


        workflow = Workflow(

            id=str(uuid.uuid4()),

            name="AI Generated Workflow",

            steps=[

                WorkflowStep(

                    id="research",

                    agent="ResearchAgent",

                    task="Pesquisar mercado e tendências"

                ),

                WorkflowStep(

                    id="product",

                    agent="ProductAgent",

                    task="Criar produto digital"

                ),

                WorkflowStep(

                    id="marketing",

                    agent="MarketingAgent",

                    task="Criar página de vendas e estratégia"

                ),

                WorkflowStep(

                    id="automation",

                    agent="AutomationAgent",

                    task="Automatizar divulgação"

                )

            ]

        )


        return workflow