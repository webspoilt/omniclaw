from fastapi import APIRouter, HTTPException
from database import SessionLocal, CostEntry
from models import CostRecord
from typing import List

router = APIRouter(prefix="/api/costs", tags=["costs"])

@router.get("/", response_model=List[CostRecord])
async def get_costs(limit: int = 100):
    db = SessionLocal()
    costs = db.query(CostEntry).order_by(CostEntry.timestamp.desc()).limit(limit).all()
    db.close()
    return [
        CostRecord(
            id=c.id,
            timestamp=c.timestamp,
            model=c.model,
            prompt_tokens=c.prompt_tokens,
            completion_tokens=c.completion_tokens,
            cost_usd=c.cost_usd,
            agent=c.agent
        ) for c in costs
    ]
