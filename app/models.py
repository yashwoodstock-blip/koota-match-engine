"""SQLAlchemy models for Koota Match Engine."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Koota(Base):
    __tablename__ = "kootas"

    koota_id = Column(Integer, primary_key=True, index=True)
    pillar = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    weight = Column(Integer, nullable=False)
    question_type = Column(String(50), nullable=False)  # mixed, objective_only, subjective_only
    is_hard_filter = Column(Boolean, default=False, nullable=False)
    objective_questions = Column(JSON, default=list, nullable=False)
    subjective_questions = Column(JSON, default=list, nullable=False)

    answers = relationship("Answer", back_populates="koota", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Koota id={self.koota_id} name='{self.name}' weight={self.weight}>"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=True)
    religion = Column(String(100), nullable=False)
    caste = Column(String(100), nullable=True)
    caste_preference = Column(String(100), nullable=True)  # "no_preference", "same_caste_preferred", "same_caste_required"
    city = Column(String(100), nullable=True)
    invite_code = Column(String(32), nullable=True, index=True)
    last_refreshed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    answers = relationship("Answer", back_populates="profile", cascade="all, delete-orphan")
    weekly_matches = relationship(
        "WeeklyMatchList",
        foreign_keys="WeeklyMatchList.profile_id",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    following_list = relationship(
        "FollowingList",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Profile id='{self.id}' name='{self.name}' age={self.age}>"


class FollowingList(Base):
    __tablename__ = "following_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    usernames = Column(JSON, default=list, nullable=False)  # Normalized list of lowercased, deduplicated usernames
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    opted_in = Column(Boolean, default=True, nullable=False)

    profile = relationship("Profile", back_populates="following_list")

    def __repr__(self) -> str:
        return f"<FollowingList profile='{self.profile_id}' count={len(self.usernames or [])} opted_in={self.opted_in}>"


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    koota_id = Column(Integer, ForeignKey("kootas.koota_id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)  # 0-indexed within question_type
    question_type = Column(String(50), nullable=False)  # "objective" or "subjective"
    raw_value = Column(Text, nullable=False)  # raw answer text or option value
    embedding = Column(JSON, nullable=True)  # List of 384 floats for subjective questions
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="answers")
    koota = relationship("Koota", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("profile_id", "koota_id", "question_index", "question_type", name="uq_profile_koota_question"),
    )

    def __repr__(self) -> str:
        return f"<Answer profile='{self.profile_id}' koota={self.koota_id} q_idx={self.question_index} type='{self.question_type}'>"


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_a_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_b_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    is_viable = Column(Boolean, nullable=False)
    hard_filter_reason = Column(String(255), nullable=True)
    overall_score = Column(Float, nullable=True)
    tier = Column(String(100), nullable=False)  # "not viable", "compatible with flagged friction points", "strong match"
    objective_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    disagreement_flags = Column(JSON, default=list, nullable=False)
    alignment_points = Column(JSON, default=list, nullable=False)
    friction_points = Column(JSON, default=list, nullable=False)
    social_overlap_score = Column(Float, default=0.0, nullable=True)
    shared_account_count = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<MatchResult a='{self.profile_a_id}' b='{self.profile_b_id}' tier='{self.tier}' score={self.overall_score}>"


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    created_by = Column(String(100), default="admin", nullable=False)
    used_by = Column(String(255), nullable=True)  # email or profile_id
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<InviteCode code='{self.code}' used_by='{self.used_by}'>"


class WeeklyMatchList(Base):
    __tablename__ = "weekly_match_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    tier = Column(String(100), nullable=False)  # "strong match", "compatible with flagged friction points", etc.
    alignment_points = Column(JSON, default=list, nullable=False)
    friction_points = Column(JSON, default=list, nullable=False)
    contradiction_gates = Column(JSON, default=list, nullable=False)
    social_overlap_score = Column(Float, default=0.0, nullable=True)
    shared_account_count = Column(Integer, default=0, nullable=True)
    generated_at = Column(DateTime, default=utc_now, nullable=False)

    profile = relationship("Profile", foreign_keys=[profile_id], back_populates="weekly_matches")
    candidate = relationship("Profile", foreign_keys=[candidate_id])

    def __repr__(self) -> str:
        return f"<WeeklyMatchList profile='{self.profile_id}' candidate='{self.candidate_id}' score={self.score}>"


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    target_profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    expressed_at = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # "pending" | "mutual" | "declined"

    __table_args__ = (
        UniqueConstraint("profile_id", "target_profile_id", name="uq_interest_pair"),
    )

    def __repr__(self) -> str:
        return f"<Interest from='{self.profile_id}' to='{self.target_profile_id}' status='{self.status}'>"


class CompatibilityCode(Base):
    __tablename__ = "compatibility_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    creator_profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_by_profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    used_at = Column(DateTime, nullable=True)

    creator = relationship("Profile", foreign_keys=[creator_profile_id])
    used_by = relationship("Profile", foreign_keys=[used_by_profile_id])

    def __repr__(self) -> str:
        return f"<CompatibilityCode code='{self.code}' creator='{self.creator_profile_id}' is_used={self.is_used}>"

