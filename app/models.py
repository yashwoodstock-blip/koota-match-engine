"""SQLAlchemy models for Koota Match Engine."""
import uuid
from datetime import datetime
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
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=True)
    religion = Column(String(100), nullable=False)
    caste = Column(String(100), nullable=True)
    caste_preference = Column(String(100), nullable=True)  # "no_preference", "same_caste_preferred", "same_caste_required"
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    answers = relationship("Answer", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Profile id='{self.id}' name='{self.name}'>"


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    koota_id = Column(Integer, ForeignKey("kootas.koota_id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)  # 0-indexed within question_type
    question_type = Column(String(50), nullable=False)  # "objective" or "subjective"
    raw_value = Column(Text, nullable=False)  # raw answer text or option value
    embedding = Column(JSON, nullable=True)  # Cached vector as JSON float array [dim=384/etc.]

    profile = relationship("Profile", back_populates="answers")
    koota = relationship("Koota", back_populates="answers")

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MatchResult a='{self.profile_a_id}' b='{self.profile_b_id}' tier='{self.tier}' score={self.overall_score}>"
