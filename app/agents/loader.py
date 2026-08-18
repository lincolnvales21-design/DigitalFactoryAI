from app.agents.manager import manager

from app.agents.research_agent import ResearchAgent
from app.agents.product_agent import ProductAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.automation_agent import AutomationAgent

from app.agents.router import AgentRouter


def load_agents():

    if manager.list_agents():
        return manager


    research_agent = ResearchAgent()
    manager.register(research_agent)


    product_agent = ProductAgent()
    manager.register(product_agent)


    marketing_agent = MarketingAgent()
    manager.register(marketing_agent)


    router = AgentRouter(manager)


    automation_agent = AutomationAgent(router, manager)
    manager.register(automation_agent)


    return manager
