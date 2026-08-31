from app.agents.manager import manager
from app.memory.agent_memory import memory
from app.security.emergency_stop import emergency_stop


class PlanExecutor:

    async def execute(self, plan):

        # Verifica se o sistema está parado
        if emergency_stop.is_active():

            return {
                "status": "stopped",
                "reason": emergency_stop.status()["reason"],
                "objective": plan.objective,
                "results": []
            }

        results = []

        for step in plan.steps:

            agent = self.find_agent(step.agent)

            if agent:

                context = self.get_context(step)

                task = step.task

                if context:

                    task = f"""
{step.task}

Contexto anterior:
{context}
"""

                result = await agent.execute_task(task)

                results.append(
                    {
                        "id": step.id,
                        "agent": step.agent,
                        "task": task,
                        "result": result
                    }
                )

            else:

                results.append(
                    {
                        "agent": step.agent,
                        "error": "Agent not found"
                    }
                )

        return {
            "objective": plan.objective,
            "results": results
        }

    def get_context(self, step):

        if not step.depends_on:
            return None

        contexts = []

        for dependency in step.depends_on:

            for agent in manager.agents:

                if agent.name.lower().startswith(dependency.lower()):

                    result = memory.get_latest_result(agent.name)

                    if result:
                        contexts.append(result)

        if contexts:
            return contexts[-1]

        return None

    def find_agent(self, name):

        for agent in manager.agents:

            if agent.name.lower() == name.lower():
                return agent

        return None


executor = PlanExecutor()