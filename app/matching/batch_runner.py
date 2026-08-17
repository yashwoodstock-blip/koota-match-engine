"""Scheduled weekly batch runner to precompute matches for all complete profiles."""
import asyncio
import time
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.models import Profile, Answer, Koota
from app.api.routes_match import load_kootas_metadata
from app.matching.candidates_batch import run_candidates_funnel_for_profile


class GroqRateLimiter:
    """Token bucket / sliding window rate limiter ensuring < 30 calls per 60 seconds."""

    def __init__(self, max_requests: int = 25, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: List[float] = []

    async def acquire(self):
        """Wait if necessary before allowing next API request."""
        now = time.time()
        # Filter timestamps within current window
        self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
        if len(self.timestamps) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.timestamps[0]) + 0.1
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self.timestamps = [t for t in self.timestamps if time.time() - t < self.window_seconds]

        self.timestamps.append(time.time())


async def get_all_complete_profile_ids(db: AsyncSession) -> List[str]:
    """Retrieve all profile IDs that have submitted substantial answers."""
    stmt = (
        select(Answer.profile_id)
        .group_by(Answer.profile_id)
        .having(func.count(Answer.id) >= 5)
    )
    res = await db.execute(stmt)
    active_ids = list(res.scalars().all())
    # Sort synthetic profiles first
    active_ids.sort(key=lambda x: (not x.startswith("syn-"), x))
    return active_ids


async def run_weekly_matching_batch(max_users: Optional[int] = None):
    """Sequentially execute candidate funnels across all active users."""
    print("=== Starting Weekly Match Precomputation Batch Job ===", flush=True)
    start_time = time.time()

    async with async_session() as db:
        kootas_meta = await load_kootas_metadata(db)
        profile_ids = await get_all_complete_profile_ids(db)

    if max_users:
        profile_ids = profile_ids[:max_users]

    print(f"Identified {len(profile_ids)} candidate profiles for weekly matching.", flush=True)
    total_matches_generated = 0

    for idx, pid in enumerate(profile_ids, 1):
        print(f"[{idx}/{len(profile_ids)}] Computing weekly match funnel for profile: {pid}...", flush=True)
        async with async_session() as db:
            matches = await run_candidates_funnel_for_profile(
                profile_id=pid,
                db=db,
                kootas_metadata=kootas_meta,
                max_weekly_matches=5,
            )
            total_matches_generated += len(matches)
            print(f"  -> Generated {len(matches)} matches (Top score: {matches[0].score if matches else 'N/A'})", flush=True)

        # Brief rate limiting buffer between users to respect 30 RPM ceiling
        await asyncio.sleep(0.5)

    elapsed = round(time.time() - start_time, 2)
    print(f"=== Weekly Match Batch Completed in {elapsed}s. Total matches stored: {total_matches_generated} ===", flush=True)


if __name__ == "__main__":
    asyncio.run(run_weekly_matching_batch())
