"""Seed Koota table from kootas.json specification."""
import asyncio
import json
import os
from pathlib import Path
from sqlalchemy import select
from app.db.session import engine, init_db, async_session
from app.models import Koota


async def seed_kootas(json_path: Path = None) -> int:
    """Read kootas.json and populate the Koota table in DB."""
    if json_path is None:
        json_path = Path(__file__).parent / "kootas.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Kootas specification file not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize tables
    await init_db()

    count = 0
    async with async_session() as session:
        for item in data:
            stmt = select(Koota).where(Koota.koota_id == item["koota_id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.pillar = item["pillar"]
                existing.name = item["name"]
                existing.weight = item["weight"]
                existing.question_type = item["question_type"]
                existing.is_hard_filter = item["is_hard_filter"]
                existing.objective_questions = item["objective_questions"]
                existing.subjective_questions = item["subjective_questions"]
            else:
                koota = Koota(
                    koota_id=item["koota_id"],
                    pillar=item["pillar"],
                    name=item["name"],
                    weight=item["weight"],
                    question_type=item["question_type"],
                    is_hard_filter=item["is_hard_filter"],
                    objective_questions=item["objective_questions"],
                    subjective_questions=item["subjective_questions"],
                )
                session.add(koota)
            count += 1

        await session.commit()

        # Verify count
        stmt_count = select(Koota)
        res = await session.execute(stmt_count)
        all_kootas = res.scalars().all()
        print(f"Successfully seeded/verified {len(all_kootas)} Kootas into the database.")
        return len(all_kootas)


if __name__ == "__main__":
    total = asyncio.run(seed_kootas())
    print(f"Total active Kootas: {total}/42")
