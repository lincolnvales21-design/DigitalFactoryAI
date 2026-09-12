from app.agents.manager import manager

from app.agents.research_agent import ResearchAgent
from app.agents.product_agent import ProductAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.automation_agent import AutomationAgent

from app.agents.router import AgentRouter


def _ensure_agent(agent_name, factory):
    if manager.get_agent(agent_name) is None:
        manager.register(factory())


def load_agents():

    _ensure_agent(
        "ResearchAgent",
        ResearchAgent,
    )

    _ensure_agent(
        "ProductAgent",
        ProductAgent,
    )

    _ensure_agent(
        "MarketingAgent",
        MarketingAgent,
    )

    router = AgentRouter(manager)

    if manager.get_agent("AutomationAgent") is None:
        automation_agent = AutomationAgent(router, manager)
        manager.register(automation_agent)

    return manager
