from app.agents.registry import registry


class BaseAgent:


    def __init__(self, name):

        self.name = name
        self.capabilities = []

        registry.register(self)


    def add_capability(self, capability):

        self.capabilities.append(capability)


    def get_info(self):

        return {
            "name": self.name,
            "capabilities": self.capabilities
        }