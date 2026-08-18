"""Phase 1 Scaffolding and Seed Verification Tests."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.db.seed_kootas import seed_kootas
from app.models import Koota
from app.db.session import async_session
from sqlalchemy import select


def test_kootas_json_structure():
    """Verify all 42 Kootas exist with complete schema in kootas.json."""
    json_path = Path(__file__).parent.parent / "app" / "db" / "kootas.json"
    assert json_path.exists(), "kootas.json must exist"

    with open(json_path, "r", encoding="utf-8") as f:
        kootas = json.load(f)

    assert len(kootas) == 42, f"Expected 42 Kootas, got {len(kootas)}"

    koota_ids = set()
    for k in kootas:
        assert "koota_id" in k
        assert "pillar" in k
        assert "name" in k
        assert "weight" in k
        assert "question_type" in k
        assert "is_hard_filter" in k
        assert "aggregation_type" in k
        assert k["aggregation_type"] in ["compensatory", "non_compensatory"]
        assert "objective_questions" in k
        assert "subjective_questions" in k
        assert 1 <= k["koota_id"] <= 42
        assert k["weight"] >= 1
        koota_ids.add(k["koota_id"])

    assert len(koota_ids) == 42, "All Koota IDs must be unique from 1 to 42"


@pytest.mark.asyncio
async def test_seed_kootas_database():
    """Verify seed_kootas populates 42 rows in database."""
    total = await seed_kootas()
    assert total == 42

    async with async_session() as session:
        result = await session.execute(select(Koota))
        records = result.scalars().all()
        assert len(records) == 42
        
        # Verify koota 18 (In-Law Relationship Expectations - w14, compensatory)
        k18 = next((k for k in records if k.koota_id == 18), None)
        assert k18 is not None
        assert k18.weight == 14
        assert k18.aggregation_type == "compensatory"
        assert len(k18.objective_questions) == 2
        assert len(k18.subjective_questions) == 2

        # Verify koota 41 (Life Purpose & Meaning of Marriage - w15, non_compensatory)
        k41 = next((k for k in records if k.koota_id == 41), None)
        assert k41 is not None
        assert k41.weight == 15
        assert k41.aggregation_type == "non_compensatory"
        assert k41.tau_low == 0.50
        assert k41.tau_high == 0.80
        assert k41.floor == 0.30
        assert k41.question_type == "subjective_only"

        # Verify koota 42 (Caste & Community Preference - is_hard_filter=True)
        k42 = next((k for k in records if k.koota_id == 42), None)
        assert k42 is not None
        assert k42.is_hard_filter is True


def test_health_endpoint():
    """Verify FastAPI health check endpoint returns 200 and validates DB readiness."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert data["service"] == "koota-match-engine"

