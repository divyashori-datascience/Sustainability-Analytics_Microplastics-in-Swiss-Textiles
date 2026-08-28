"""
Data models.

Covers: Session, raw answers, greenwashing flags, and the two Stage 1 outputs
(Certification Relevance Map + Internal Greenwashing Risk Assessment).
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ── Enumerations ─────────────────────────────────────────────────────────────

class FlagPriority(str, Enum):
    CRITICAL = "critical"   # blocks platform access pending review
    MODERATE = "moderate"   # follow-up required before Stage 2
    LOW      = "low"        # to be addressed in Stage 2

class ClaimStatus(str, Enum):
    SUBSTANTIATED         = "substantiated"
    PARTIALLY_SUBSTANTIATED = "partially_substantiated"
    UNSUBSTANTIATED       = "unsubstantiated"
    CONTRADICTED          = "contradicted"

class OverallRisk(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED   = "red"

class FrameworkRelevance(str, Enum):
    RELEVANT   = "relevant"
    EXCLUDED   = "excluded"

class SessionStatus(str, Enum):
    ACTIVE    = "active"
    COMPLETE  = "complete"
    ABANDONED = "abandoned"

class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"


# ── Raw answer store ──────────────────────────────────────────────────────────

class QuestionAnswer(BaseModel):
    question_id: str
    raw_answer: str                          # verbatim as given by the brand
    structured: dict[str, Any] = Field(default_factory=dict)  # parsed fields
    answered_at: datetime = Field(default_factory=datetime.utcnow)


# ── Greenwashing flags ────────────────────────────────────────────────────────

class GreenwashingFlag(BaseModel):
    question_id: str
    claim: str                # the specific claim or behaviour flagged
    flag_message: str
    priority: FlagPriority
    status: ClaimStatus = ClaimStatus.UNSUBSTANTIATED

class GreenwashingRiskAssessment(BaseModel):
    """Internal output — not shared with brand."""
    flags: list[GreenwashingFlag] = Field(default_factory=list)
    claim_statuses: dict[str, ClaimStatus] = Field(default_factory=dict)
    overall_risk: OverallRisk = OverallRisk.GREEN
    analyst_notes: str = ""

    def compute_overall_risk(self) -> None:
        if any(f.priority == FlagPriority.CRITICAL for f in self.flags):
            self.overall_risk = OverallRisk.RED
        elif any(f.priority == FlagPriority.MODERATE for f in self.flags):
            self.overall_risk = OverallRisk.AMBER
        else:
            self.overall_risk = OverallRisk.GREEN


# ── Certification Relevance Map ───────────────────────────────────────────────

class FrameworkEntry(BaseModel):
    name: str
    acronym: str
    relevance: FrameworkRelevance
    reason: str                   # one-line explanation — included or excluded, why
    priority_rank: Optional[int] = None   # 1 = most relevant, set for included only

class CertificationRelevanceMap(BaseModel):
    """Brand-facing Stage 1 output."""
    session_id: str
    brand_name: Optional[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    relevant_frameworks: list[FrameworkEntry] = Field(default_factory=list)
    excluded_frameworks: list[FrameworkEntry] = Field(default_factory=list)
    analyst_summary: str = ""   # 2–3 sentence human-readable summary

    @property
    def relevant_count(self) -> int:
        return len(self.relevant_frameworks)


# ── Session ───────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE

    # All raw answers keyed by question ID
    answers: dict[str, QuestionAnswer] = Field(default_factory=dict)

    # Questions answered so far (in order)
    answered_question_ids: list[str] = Field(default_factory=list)

    # Conversation history
    messages: list[Message] = Field(default_factory=list)
    turn_count: int = 0

    # Stage 1 outputs (populated when all 21 questions answered)
    relevance_map: Optional[CertificationRelevanceMap] = None
    greenwashing_assessment: Optional[GreenwashingRiskAssessment] = None

    # Convenience: extracted key facts for framework matching
    facts: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self.turn_count += 1

    def record_answer(self, question_id: str, raw_answer: str, structured: dict = None) -> None:
        self.answers[question_id] = QuestionAnswer(
            question_id=question_id,
            raw_answer=raw_answer,
            structured=structured or {}
        )
        if question_id not in self.answered_question_ids:
            self.answered_question_ids.append(question_id)

    def get_answer(self, question_id: str) -> Optional[str]:
        ans = self.answers.get(question_id)
        return ans.raw_answer if ans else None

    @property
    def questions_answered(self) -> int:
        return len(self.answered_question_ids)

    @property
    def conversation_history(self) -> list[dict]:
        return [{"role": m.role.value, "content": m.content} for m in self.messages]

    @property
    def _total_questions(self) -> int:
        from .questions_stage1 import STAGE1_QUESTIONS
        return len(STAGE1_QUESTIONS)

    @property
    def progress_pct(self) -> int:
        total = self._total_questions
        return round(self.questions_answered / total * 100) if total else 0

    @property
    def unanswered_question_ids(self) -> list[str]:
        from .questions_stage1 import STAGE1_QUESTIONS
        answered = set(self.answered_question_ids)
        return [q.id for q in STAGE1_QUESTIONS if q.id not in answered]
