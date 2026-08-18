"""Test privacy boundaries of compatibility-code generator responses."""
import pytest
from app.main import app
from fastapi.testclient import TestClient
from tests.test_on_demand_refresh_and_compatibility import create_test_profile, populate_minimal_answers

client = TestClient(app)


@pytest.mark.asyncio
async def test_compatibility_codes_generator_response_privacy_leak_protection():
    """Verify GET /profiles/{id}/compatibility-codes returns ONLY CandidateMatchSummary and no raw profile data."""
    creator_id = await create_test_profile(name="Generator A", age=28, religion="Hindu")
    redeemer_id = await create_test_profile(name="Redeemer B", age=29, religion="Hindu")
    await populate_minimal_answers(creator_id)
    await populate_minimal_answers(redeemer_id)

    # 1. Generator creates code
    res_code = client.post(
        f"/profiles/{creator_id}/compatibility-code",
        headers={"X-Test-Profile-Id": creator_id},
    )
    code = res_code.json()["code"]

    # 2. Redeemer redeems code
    client.post(
        f"/profiles/{redeemer_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": redeemer_id},
    )

    # 3. Creator retrieves code list
    res_list = client.get(
        f"/profiles/{creator_id}/compatibility-codes",
        headers={"X-Test-Profile-Id": creator_id},
    )
    assert res_list.status_code == 200
    data = res_list.json()

    codes = data.get("codes", [])
    target = next((c for c in codes if c["code"] == code), None)
    assert target is not None
    assert target["is_used"] is True

    match_result = target["match_result"]
    assert match_result is not None

    # Strict contract verification: exactly CandidateMatchSummary allowed keys
    allowed_keys = {
        "candidate_id",
        "candidate_name",
        "is_viable",
        "tier",
        "overall_score",
        "compensatory_score",
        "ceiling_applied",
        "capped_by",
        "risk_adjusted_score",
        "score_uncertainty",
        "score_interval",
        "confidence",
        "evidence_coverage_pct",
        "critical_contradictions",
        "high_impact_uncertainty",
        "alignment_points",
        "friction_points",
        "disagreement_count",
        "contradiction_count",
        "social_overlap_score",
        "shared_account_count",
    }

    match_keys = set(match_result.keys())
    # Confirm no private leaks
    assert match_keys.issubset(allowed_keys)
    forbidden_keys = {
        "email",
        "phone",
        "answers",
        "raw_answers",
        "subjective_answers",
        "city",
        "income",
        "address",
        "family_details",
    }
    assert forbidden_keys.isdisjoint(match_keys)
