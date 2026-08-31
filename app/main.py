from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

from fastapi import FastAPI
from app.database.init_db import init_database
from app.api import planner
from app.api import agents
from app.api import automation
from app.api import memory
from app.api import products
from app.api import orders
from app.api import payments
from app.api import delivery
from app.api import finance
from app.api import business

from app.api.admin.security import router as security_router
from app.api.admin.secret import router as secret_router
from app.api.admin.agent_guard import router as agent_guard_router

from app.agents.registry import registry
from app.agents.manager import manager
from app.agents.router import AgentRouter


# ==========================
# FastAPI
# ==========================

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="DigitalFactoryAI",
    description="AI Multi-Agent Automation Platform",
    version="0.1.0",
    lifespan=lifespan
)


# ==========================
# Import dos Agentes
# ==========================

from app.agents.loader import load_agents


load_agents()


# ==========================
# Inicialização dos Agentes
# ==========================

from app.agents.loader import load_agents

load_agents()



# ==========================
# Registrar APIs
# ==========================

app.include_router(planner.router)
app.include_router(agents.router)
app.include_router(automation.router)
app.include_router(memory.router)
app.include_router(security_router)
app.include_router(secret_router)
app.include_router(agent_guard_router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(delivery.router)
app.include_router(finance.router)
app.include_router(business.router)

# ==========================
# Health Check
# ==========================

@app.get("/")
def home():

    return {
        "system": "DigitalFactoryAI",
        "status": "online",
        "message": "AI Factory running"
    }


# ==========================
# Agent Registry
# ==========================

@app.get("/registry")
def registry_info():

    return registry.list_capabilities()