"""Pytest configuration and database initialization fixture."""
import asyncio
import pytest
from app.db.session import init_db


@pytest.fixture(autouse=True, scope="session")
def initialize_test_database():
    """Ensure all database tables and schema migrations are applied before running test suite."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    loop.close()
