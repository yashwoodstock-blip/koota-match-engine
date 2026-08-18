"""Test suite for Phase 7 Following List API and privacy boundaries."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.session import async_session
from app.models import Profile, FollowingList, WeeklyMatchList, utc_now
from app.auth.invite import create_invite_session_token


@pytest.fixture
def registered_profile_ids():
    """Create two test profiles with valid invite tokens for API testing."""
    token_a = create_invite_session_token("INVITE_F1")
    token_b = create_invite_session_token("INVITE_F2")

    with TestClient(app) as client:
        res_a = client.post("/profiles", json={
            "name": "Social User A",
            "age": 28,
            "gender": "female",
            "religion": "Hindu",
            "caste": "Brahmin",
            "caste_preference": "no_preference",
            "city": "Bengaluru",
            "invite_token": token_a,
        })
        assert res_a.status_code == 201
        p_a_id = res_a.json()["id"]

        res_b = client.post("/profiles", json={
            "name": "Social User B",
            "age": 29,
            "gender": "male",
            "religion": "Hindu",
            "caste": "Brahmin",
            "caste_preference": "no_preference",
            "city": "Bengaluru",
            "invite_token": token_b,
        })
        assert res_b.status_code == 201
        p_b_id = res_b.json()["id"]

    return p_a_id, p_b_id


def test_following_upload_creates_row(registered_profile_ids):
    """POST /profiles/{id}/following creates a normalized FollowingList row."""
    p_a_id, _ = registered_profile_ids

    with TestClient(app) as client:
        payload = {"usernames": ["  @Virat.Kohli  ", "natgeo", "HUBERMANLAB", "natgeo"]}
        res = client.post(f"/profiles/{p_a_id}/following", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["profile_id"] == p_a_id
        assert data["account_count"] == 3
        assert data["opted_in"] is True


def test_following_reupload_replaces_row(registered_profile_ids):
    """POST /profiles/{id}/following replaces (does not append to) prior row."""
    p_a_id, _ = registered_profile_ids

    with TestClient(app) as client:
        # First upload (3 accounts)
        client.post(f"/profiles/{p_a_id}/following", json={"usernames": ["user1", "user2", "user3"]})

        # Second upload (2 new accounts)
        res2 = client.post(f"/profiles/{p_a_id}/following", json={"usernames": ["user4", "user5"]})
        assert res2.status_code == 200
        data = res2.json()
        assert data["account_count"] == 2  # Replaced, not 5


def test_following_delete_removes_row_and_is_idempotent(registered_profile_ids):
    """DELETE /profiles/{id}/following removes row and succeeds idempotently."""
    p_a_id, _ = registered_profile_ids

    with TestClient(app) as client:
        # 1. Upload first
        client.post(f"/profiles/{p_a_id}/following", json={"usernames": ["user1", "user2"]})

        # 2. Delete following list
        res_del = client.delete(f"/profiles/{p_a_id}/following")
        assert res_del.status_code == 200
        assert res_del.json()["opted_in"] is False

        # 3. Repeated delete (idempotent)
        res_del2 = client.delete(f"/profiles/{p_a_id}/following")
        assert res_del2.status_code == 200
        assert res_del2.json()["opted_in"] is False


def test_following_privacy_no_usernames_leaked_in_match_apis(registered_profile_ids, monkeypatch):
    """Assert that match endpoints never leak raw username strings in response payloads."""
    p_a_id, p_b_id = registered_profile_ids
    secret_usernames = ["secret_celebrity_x99", "private_influencer_z88", "uniquename_4421"]

    async def mock_emb(text, *args, **kwargs):
        return [0.5] * 384

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)

    with TestClient(app) as client:
        # Upload following lists with distinct unique secret usernames
        client.post(f"/profiles/{p_a_id}/following", json={"usernames": secret_usernames + ["shared_account_1"]})
        client.post(f"/profiles/{p_b_id}/following", json={"usernames": ["shared_account_1", "other_user_22"]})

        # Submit minimal answers to make profiles matchable
        answers_payload = [
            {"koota_id": 7, "question_index": 0, "question_type": "objective", "raw_value": "engage immediately"},
            {"koota_id": 7, "question_index": 1, "question_type": "objective", "raw_value": "same-day"},
            {"koota_id": 41, "question_index": 0, "question_type": "subjective", "raw_value": "Joint spiritual purpose."},
        ]
        client.post(f"/profiles/{p_a_id}/answers/batch", json={"answers": answers_payload})
        client.post(f"/profiles/{p_b_id}/answers/batch", json={"answers": answers_payload})

        # 1. Test POST /match/{a}/{b}
        res_match = client.post(f"/match/{p_a_id}/{p_b_id}")
        assert res_match.status_code == 200
        match_data = res_match.json()
        assert match_data["shared_account_count"] == 1
        assert match_data["social_overlap_score"] > 0.0

        match_text = res_match.text
        for secret_name in secret_usernames + ["shared_account_1", "other_user_22"]:
            assert secret_name not in match_text, f"Privacy violation: raw username '{secret_name}' leaked in match response!"

        # 2. Test GET /match/{id}/candidates
        res_cand = client.get(f"/match/{p_a_id}/candidates")
        assert res_cand.status_code == 200
        cand_text = res_cand.text
        for secret_name in secret_usernames:
            assert secret_name not in cand_text, f"Privacy violation: raw username '{secret_name}' leaked in candidate response!"

        # 3. Test GET /profiles/{id}/weekly-matches
        res_weekly = client.get(f"/profiles/{p_a_id}/weekly-matches", headers={"X-Test-Profile-Id": p_a_id})
        assert res_weekly.status_code == 200
        weekly_text = res_weekly.text
        for secret_name in secret_usernames:
            assert secret_name not in weekly_text, f"Privacy violation: raw username '{secret_name}' leaked in weekly match response!"
