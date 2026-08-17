"""Additive database migrations for profile and answer updated_at columns."""
from sqlalchemy import text
from app.db.session import engine


async def run_profile_update_migrations():
    """Run non-destructive additive migrations for updated_at columns."""
    async with engine.begin() as conn:
        # Check profiles table
        try:
            await conn.execute(text("ALTER TABLE profiles ADD COLUMN updated_at TIMESTAMP"))
        except Exception:
            pass  # Already exists

        # Check answers table
        try:
            await conn.execute(text("ALTER TABLE answers ADD COLUMN updated_at TIMESTAMP"))
        except Exception:
            pass  # Already exists
