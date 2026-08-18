class AgentRouter:

    def __init__(self, manager):

        self.manager = manager


    def find_agent(self, name):

        for agent in self.manager.agents:

            if agent.name == name:
                return agent

        return None


    def find_by_capability(self, capability):

        for agent in self.manager.agents:

            if capability in agent.capabilities:
                return agent

        return None


    async def auto_run(self, agent_name: str, task: str):

        agent = self.find_agent(agent_name)


        if agent is None:

            return {
                "error": f"Agente {agent_name} não encontrado"
            }


        result = await agent.execute_task(task)


        return {
            "agent": agent.name,
            "task": task,
            "result": result
        }