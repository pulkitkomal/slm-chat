from fastapi import APIRouter, HTTPException

from agents import list_agents as get_all_agents
from db import db
from models import Agent, CreateAgent

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents():
    return {"agents": get_all_agents()}


@router.post("", response_model=Agent, status_code=201)
async def create_agent(body: CreateAgent):
    agent = db.create_agent(
        name=body.name,
        avatar=body.avatar,
        title=body.title,
        system_message=body.system_message,
    )
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    if not db.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}
