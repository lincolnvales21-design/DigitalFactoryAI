from app.agents.base import BaseAgent
from app.automation.executor import WorkflowExecutor
from app.memory.agent_memory import memory


class AutomationAgent(BaseAgent):

    def __init__(self, router, manager):

        super().__init__("AutomationAgent")

        self.router = router
        self.manager = manager

        self.executor = WorkflowExecutor(router, manager)

        self.add_capability("workflow")
        self.add_capability("automation")
        self.add_capability("orchestration")


    async def execute_task(self, task: str):

        result = {
            "status": "success",
            "agent": self.name,
            "task": task,
            "message": "Automação configurada com sucesso."
        }


        memory.save(
            agent=self.name,
            task=task,
            status="completed",
            result=result
        )


        return result



    async def run_workflow(self, workflow):

        result = await self.executor.execute(
            workflow
        )


        memory.save(
            agent=self.name,
            task="Workflow executado",
            status="completed",
            result=result.to_dict()
        )


        return result