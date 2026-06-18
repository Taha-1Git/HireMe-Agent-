"""Demo Mode API endpoints.

POST /api/demo/log-event - Log a demo event
POST /api/demo/test-authenticity - Test authenticity detection with canned answer
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.core.config import settings
from app.services.agents import AuthenticityAgent
from app.models.interview import InterviewSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Only enable demo mode in development
DEMO_MODE_ENABLED = settings.debug or getattr(settings, "demo_mode", False)


class DemoEventRequest(BaseModel):
    """Request to log a demo event."""
    event_type: str
    session_id: str
    message: str
    timestamp: str


class TestAuthenticityRequest(BaseModel):
    """Request to test authenticity detection."""
    session_id: str
    candidate_answer: str
    test_label: str


class DemoEventResponse(BaseModel):
    """Response from demo event logging."""
    success: bool
    message: str
    event_type: str


@router.post("/log-event", response_model=DemoEventResponse)
async def log_demo_event(request: DemoEventRequest) -> DemoEventResponse:
    """
    Log a demo event for testing authenticity monitoring.
    
    This simulates real events for demonstration purposes.
    
    Args:
        request: Demo event details
        
    Returns:
        DemoEventResponse with success confirmation
        
    Raises:
        403: If demo mode is not enabled
    """
    if not DEMO_MODE_ENABLED:
        raise HTTPException(status_code=403, detail="Demo mode is not enabled")

    try:
        logger.info(
            f"[DEMO] Event logged: {request.event_type} - {request.message} "
            f"(session: {request.session_id})"
        )

        return DemoEventResponse(
            success=True,
            message=f"Demo event '{request.event_type}' logged successfully",
            event_type=request.event_type,
        )

    except Exception as e:
        logger.error(f"Failed to log demo event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log demo event")


@router.post("/test-authenticity")
async def test_authenticity_detection(request: TestAuthenticityRequest) -> dict:
    """
    Test authenticity detection with a canned answer.
    
    This runs the answer through the REAL AuthenticityAgent to demonstrate
    its detection capabilities. Only the input is canned, the detection logic
    is real.
    
    Args:
        request: Test parameters including canned answer
        
    Returns:
        Dict with authenticity agent analysis
        
    Raises:
        403: If demo mode is not enabled
        404: If session not found
        500: If agent processing fails
    """
    if not DEMO_MODE_ENABLED:
        raise HTTPException(status_code=403, detail="Demo mode is not enabled")

    try:
        # Load session to get CV profile for context
        from sqlmodel import create_engine

        engine = create_engine(settings.database_url)
        session = Session(engine)

        statement = select(InterviewSession).where(
            InterviewSession.session_id == request.session_id
        )
        interview_session = session.exec(statement).first()

        if not interview_session:
            raise HTTPException(status_code=404, detail="Session not found")

        cv_profile = interview_session.get_cv_profile()

        # Run through real AuthenticityAgent
        agent = AuthenticityAgent()

        # Build a mock transcript with the canned answer
        transcript = [
            {
                "role": "assistant",
                "content": "Tell me about one of your projects",
                "agent": "project_deepdive",
            },
            {"role": "user", "content": request.candidate_answer},
        ]

        # Analyze authenticity
        concern = agent.analyze_answer(
            answer=request.candidate_answer,
            cv_profile=cv_profile,
            transcript=transcript,
        )

        logger.info(
            f"[DEMO] Authenticity test '{request.test_label}' completed: "
            f"concern_score={concern.get('authenticity_concern', 0)}, "
            f"flags={concern['flags']}"
        )

        return {
            "success": True,
            "test_label": request.test_label,
            "answer": request.candidate_answer,
            "authenticity_analysis": concern,
            "interpretation": {
                "concern_score": concern.get("authenticity_concern", 0),
                "severity": "high" if float(concern.get("authenticity_concern", 0)) > 0.7 else "medium" if float(concern.get("authenticity_concern", 0)) > 0.3 else "low",
                "message": concern.get("summary", "Analysis complete"),
                "note": "This answer was processed through the REAL AuthenticityAgent. "
                "The input is canned for demo purposes, but the detection logic is genuine.",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test authenticity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authenticity test failed: {str(e)}")


@router.get("/status")
async def demo_mode_status() -> dict:
    """Get current demo mode status."""
    return {
        "demo_mode_enabled": DEMO_MODE_ENABLED,
        "message": "Demo mode enabled. Use /api/demo/log-event and /api/demo/test-authenticity endpoints."
        if DEMO_MODE_ENABLED
        else "Demo mode is disabled (set DEBUG=true or DEMO_MODE=true to enable)",
    }
