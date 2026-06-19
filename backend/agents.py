from db import db
from models import Agent as AgentModel


def get_agent(agent_id: str) -> AgentModel | None:
    return db.get_agent(agent_id)


def list_agents() -> list[AgentModel]:
    return db.list_agents()
