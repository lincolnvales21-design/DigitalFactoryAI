from app.agents.base import BaseAgent
from app.security.agent_guard import agent_guard
from app.security.permissions import Role


class AgentManager:

    def __init__(self):

        self.agents = []


    def register(self, agent: BaseAgent):

        for existing in self.agents:

            if existing.name == agent.name:
                return

        self.agents.append(agent)



    def get_agent(self, name: str):

        for agent in self.agents:

            if agent.name == name:
                return agent

        return None



    async def execute(
        self,
        role: Role,
        action: str,
        agent_name: str,
        task: str
    ):


        # 🛡️ Verificação de segurança

        authorization = agent_guard.authorize(
            role,
            action,
            agent_name
        )


        if not authorization["allowed"]:

            return authorization



        # localizar agente

        agent = self.get_agent(agent_name)


        if agent is None:

            return {
                "status": "error",
                "message": f"Agente {agent_name} não encontrado"
            }



        # executar

        result = await agent.execute_task(task)



        return {

            "status": "success",

            "authorization": authorization,

            "execution": result

        }



    def list_agents(self):

        return [
            agent.get_info()
            for agent in self.agents
        ]



manager = AgentManager()