"""Test field-name and logic consistency between objective hard filters and profile patch endpoints."""
import pytest
from app.models import Profile
from app.scoring.objective import check_hard_filters
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.asyncio
async def test_hard_filter_fields_consistency_and_patch_detection():
    """Verify check_hard_filters and PATCH /profiles/{id} stay in sync for hard-filter field names and rules."""
    # 1. Age gap consistency
    p1 = Profile(
        id="hf-prof-1",
        name="Candidate 1",
        age=28,
        gender="male",
        religion="Hindu",
        caste="Brahmin",
        caste_preference="same_caste_required",
    )
    p2 = Profile(
        id="hf-prof-2",
        name="Candidate 2",
        age=32,  # 4 years gap > 2
        gender="female",
        religion="Hindu",
        caste="Brahmin",
        caste_preference="same_caste_required",
    )
    res_age = check_hard_filters(p1, p2, max_age_gap=2)
    assert res_age.passed is False
    assert "Age gap" in res_age.reason

    # 2. Religion mismatch consistency
    p2.age = 28
    p2.religion = "Jain"
    res_rel = check_hard_filters(p1, p2)
    assert res_rel.passed is False
    assert "Religion mismatch" in res_rel.reason

    # 3. Caste requirement consistency
    p2.religion = "Hindu"
    p2.caste = "Kshatriya"
    res_caste = check_hard_filters(p1, p2)
    assert res_caste.passed is False
    assert "Caste requirement failed" in res_caste.reason

    # 4. Same caste matches
    p2.caste = "Brahmin"
    res_ok = check_hard_filters(p1, p2)
    assert res_ok.passed is True


@pytest.mark.asyncio
async def test_patch_profile_hard_filter_detection_flags():
    """Verify PATCH /profiles/{id} returns hard_filter_changed=True on religion, age, gender, and caste shifts."""
    from tests.test_on_demand_refresh_and_compatibility import create_test_profile

    p_id = await create_test_profile(
        name="Demographic User",
        age=27,
        gender="female",
        religion="Hindu",
        caste="Agarwal",
        caste_preference="same_caste_required",
    )

    # A. Minor non-hard filter update (name, city) -> hard_filter_changed=False
    res_minor = client.patch(
        f"/profiles/{p_id}",
        json={"name": "Demographic User Updated", "city": "Bangalore"},
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res_minor.status_code == 200
    assert res_minor.json()["hard_filter_changed"] is False

    # B. Religion update -> hard_filter_changed=True
    res_rel = client.patch(
        f"/profiles/{p_id}",
        json={"religion": "Jain"},
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res_rel.status_code == 200
    assert res_rel.json()["hard_filter_changed"] is True

    # C. Caste preference update -> hard_filter_changed=True
    res_caste_pref = client.patch(
        f"/profiles/{p_id}",
        json={"caste_preference": "open_to_all"},
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res_caste_pref.status_code == 200
    assert res_caste_pref.json()["hard_filter_changed"] is True

