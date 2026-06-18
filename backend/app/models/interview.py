"""SQLModel database models for TrueHire AI."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, field_validator
import json


class CVProfile(BaseModel):
    """Parsed CV profile extracted by OpenAI."""
    skills: list[str]
    projects: list[dict]  # {name, description, technologies}
    education: list[dict]  # {degree, institution, field}
    experience: list[dict]  # {title, company, duration, description}
    claimed_technologies: list[str]

    @field_validator('skills', 'claimed_technologies', mode='before')
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class InterviewSession(SQLModel, table=True):
    """Interview session record."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, index=True)
    cv_profile: str  # JSON string of CVProfile
    conversation_transcript: list[dict] = Field(default_factory=list)  # List of {role, content, agent}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Interview state
    current_agent: Optional[str] = None
    suspicion_score: float = 0.0
    authenticity_flags: list[dict] = Field(default_factory=list)  # {agent, flag, description}
    completed: bool = False
    final_report: Optional[str] = None  # JSON string of evaluation report

    def get_cv_profile(self) -> CVProfile:
        """Parse CV profile from JSON."""
        return CVProfile(**json.loads(self.cv_profile))

    def set_cv_profile(self, profile: CVProfile):
        """Store CV profile as JSON."""
        self.cv_profile = profile.model_dump_json()

    def add_message(self, role: str, content: str, agent: Optional[str] = None):
        """Add a message to the transcript."""
        self.conversation_transcript.append({
            "role": role,
            "content": content,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()


# Request/Response schemas
class CVUploadResponse(BaseModel):
    """Response from CV upload endpoint."""
    session_id: str
    profile: CVProfile
    message: str


class InterviewStartResponse(BaseModel):
    """Response from interview start endpoint."""
    session_id: str
    agent: str
    opening_question: str
    message: str


class CandidateAnswerRequest(BaseModel):
    """Request body for candidate answer."""
    answer: str


class InterviewAnswerResponse(BaseModel):
    """Response from answer endpoint."""
    session_id: str
    agent_name: str
    evaluation: str
    next_question: str
    suspicion_delta: float
    authenticity_flags: list[dict]


class FinalReportResponse(BaseModel):
    """Final evaluation report."""
    session_id: str
    technical_score: int  # 0-100
    communication_score: int  # 0-100
    cv_authenticity: str  # "High"/"Medium"/"Low"
    cheating_risk: str  # "Low"/"Medium"/"High"
    recommendation: str  # "Shortlist"/"Manual review required"/"Reject"
    justification: str
    agent_flags: list[dict]
    transcript: list[dict]
