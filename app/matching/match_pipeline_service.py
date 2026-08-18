"""Shared service helpers for matching pipeline operations and Koota metadata loading."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Koota


async def load_kootas_metadata(db: AsyncSession) -> Dict[int, Dict[str, Any]]:
    """Load metadata for all 42 Kootas into a fast in-memory lookup dictionary."""
    stmt = select(Koota)
    res = await db.execute(stmt)
    kootas = res.scalars().all()
    return {
        k.koota_id: {
            "weight": k.weight,
            "name": k.name,
            "pillar": k.pillar,
            "question_type": k.question_type,
            "is_hard_filter": k.is_hard_filter,
            "subjective_questions": k.subjective_questions,
            "objective_questions": k.objective_questions,
        }
        for k in kootas
    }


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime object is explicitly UTC timezone-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
