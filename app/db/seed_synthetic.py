"""Seed database with synthetic test profiles from tests/synthetic_profiles.json."""
import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from app.db.session import engine, init_db, async_session
from app.models import Profile, Answer
from app.db.seed_kootas import seed_kootas


async def seed_synthetic_profiles(json_path: Path = None) -> int:
    """Read synthetic_profiles.json and populate Profile & Answer tables."""
    if json_path is None:
        json_path = Path(__file__).parent.parent.parent / "tests" / "synthetic_profiles.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Synthetic profiles file not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)

    # Ensure DB & Kootas are initialized
    await init_db()
    await seed_kootas()

    count = 0
    async with async_session() as session:
        for p_dict in profiles_data:
            # Check or create profile
            stmt = select(Profile).where(Profile.id == p_dict["id"])
            res = await session.execute(stmt)
            profile = res.scalar_one_or_none()

            if not profile:
                profile = Profile(
                    id=p_dict["id"],
                    name=p_dict["name"],
                    age=p_dict["age"],
                    gender=p_dict.get("gender"),
                    religion=p_dict["religion"],
                    caste=p_dict.get("caste"),
                    caste_preference=p_dict.get("caste_preference", "no_preference"),
                    city=p_dict.get("city"),
                )
                session.add(profile)
                await session.flush()

            # Add answers
            for a_dict in p_dict.get("answers", []):
                ans_stmt = select(Answer).where(
                    Answer.profile_id == profile.id,
                    Answer.koota_id == a_dict["koota_id"],
                    Answer.question_index == a_dict["question_index"],
                    Answer.question_type == a_dict["question_type"],
                )
                ans_res = await session.execute(ans_stmt)
                if not ans_res.scalar_one_or_none():
                    ans = Answer(
                        profile_id=profile.id,
                        koota_id=a_dict["koota_id"],
                        question_index=a_dict["question_index"],
                        question_type=a_dict["question_type"],
                        raw_value=a_dict["raw_value"],
                    )
                    session.add(ans)

            count += 1

        await session.commit()
        print(f"Successfully seeded {count} synthetic profiles and their answers into the database.")
        return count


if __name__ == "__main__":
    total = asyncio.run(seed_synthetic_profiles())
    print(f"Total synthetic profiles seeded: {total}")
