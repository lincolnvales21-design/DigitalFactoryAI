from app.automation.models import WorkflowStatus
from app.automation.planner import WorkflowPlanner
from app.security.permissions import Role


class WorkflowExecutor:

    def __init__(self, router, manager):

        self.router = router
        self.manager = manager

        self.planner = WorkflowPlanner()


    async def execute(self, workflow):

        workflow.status = WorkflowStatus.RUNNING

        while True:

            ready_steps = self.planner.get_ready_steps(
                workflow
            )

            if not ready_steps:
                break

            for step in ready_steps:

                step.status = WorkflowStatus.RUNNING

                try:

                    result = await self.manager.execute(
                        Role.OWNER,
                        "execute_agents",
                        step.agent,
                        step.task
                    )

                    if result.get("status") != "success":

                        raise Exception(
                            result.get(
                                "reason",
                                result.get(
                                    "message",
                                    "Execução do agente bloqueada"
                                )
                            )
                        )

                    step.result = result
                    step.status = WorkflowStatus.COMPLETED

                except Exception as e:

                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    workflow.status = WorkflowStatus.FAILED

                    return workflow

        workflow.status = WorkflowStatus.COMPLETED

        return workflow