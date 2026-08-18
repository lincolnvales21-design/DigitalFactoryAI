class AgentRegistry:

    def __init__(self):
        self.agents = {}


    def register(self, agent):

        name = agent.name

        if name in self.agents:
            return

        self.agents[name] = agent


    def get_agent(self, name):

        return self.agents.get(name)


    def list_agents(self):

        return list(self.agents.values())


    def list_capabilities(self):

        return [
            {
                "name": agent.name,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
        ]


    def find_by_capability(self, capability):

        for agent in self.agents.values():

            if capability in agent.capabilities:
                return agent

        return None


registry = AgentRegistry()