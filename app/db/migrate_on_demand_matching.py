"""Additive database migrations for on-demand match refresh and compatibility codes."""
from sqlalchemy import text
from app.db.session import engine


async def run_on_demand_matching_migrations():
    """Run non-destructive additive migrations for last_refreshed_at and compatibility_codes."""
    async with engine.begin() as conn:
        # Check profiles table for last_refreshed_at
        try:
            await conn.execute(text("ALTER TABLE profiles ADD COLUMN last_refreshed_at TIMESTAMP"))
        except Exception:
            pass  # Already exists or handled by create_all

        # Create compatibility_codes table if not exists (handled by metadata.create_all, but additive SQL for safe migration)
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS compatibility_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(32) NOT NULL UNIQUE,
                    creator_profile_id VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT 0,
                    used_by_profile_id VARCHAR(64),
                    used_at TIMESTAMP,
                    FOREIGN KEY(creator_profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                    FOREIGN KEY(used_by_profile_id) REFERENCES profiles(id) ON DELETE SET NULL
                )
            """))
        except Exception:
            pass
