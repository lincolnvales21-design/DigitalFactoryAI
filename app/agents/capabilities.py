class AgentCapabilities:

    def __init__(self):
        self.capabilities = []


    def add(self, capability: str):
        self.capabilities.append(capability)


    def list(self):
        return self.capabilities


    def has(self, capability: str):
        return capability in self.capabilities