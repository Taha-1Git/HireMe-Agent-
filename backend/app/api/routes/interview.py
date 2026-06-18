"""Interview orchestration routes."""

import logging
import json
from fastapi import APIRouter, HTTPException, WebSocket
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models.interview import (
    InterviewSession, InterviewStartResponse, 
    CandidateAnswerRequest, InterviewAnswerResponse,
    FinalReportResponse
)
from app.services.interview import InterviewOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Database setup
engine = create_engine(settings.database_url)

# WebSocket broadcast storage (for live logs)
active_connections: dict[str, list[WebSocket]] = {}


def get_session(session_id: str) -> InterviewSession:
    """Get interview session from database."""
    with Session(engine) as db_session:
        statement = select(InterviewSession).where(InterviewSession.session_id == session_id)
        session = db_session.exec(statement).first()
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return session


def save_session(session: InterviewSession):
    """Save session to database."""
    with Session(engine) as db_session:
        db_session.add(session)
        db_session.commit()


@router.post("/start/{session_id}", response_model=InterviewStartResponse, tags=["interview"])
async def start_interview(session_id: str):
    """
    Start an interview and get the opening question.
    
    Args:
        session_id: Interview session ID from CV upload
    
    Returns:
        Opening question from the first agent
    """
    logger.info(f"Starting interview for session {session_id}")
    
    session = get_session(session_id)
    
    if session.completed:
        raise HTTPException(status_code=400, detail="Interview already completed")
    
    # Initialize orchestrator and generate opening question
    orchestrator = InterviewOrchestrator(session)
    question_obj = orchestrator.generate_opening_question()
    
    # Save updated session
    save_session(session)
    
    # Broadcast to WebSocket
    await broadcast_log(session_id, f"{question_obj['agent']}: {question_obj['question']}")
    
    return InterviewStartResponse(
        session_id=session_id,
        agent=question_obj["agent"],
        opening_question=question_obj["question"],
        message="Interview started"
    )


@router.post("/answer/{session_id}", response_model=InterviewAnswerResponse, tags=["interview"])
async def submit_answer(session_id: str, request: CandidateAnswerRequest):
    """
    Submit a candidate's answer and get the next question.
    
    Args:
        session_id: Interview session ID
        request: Candidate's answer text
    
    Returns:
        Next question and feedback from agents
    """
    logger.info(f"Submitting answer for session {session_id}")
    
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty")
    
    session = get_session(session_id)
    
    if session.completed:
        raise HTTPException(status_code=400, detail="Interview already completed")
    
    # Process answer
    orchestrator = InterviewOrchestrator(session)
    result = orchestrator.process_answer(request.answer)
    
    # Save updated session
    save_session(session)
    
    # Broadcast to WebSocket
    await broadcast_log(
        session_id,
        f"{result['agent_name']}: {result['evaluation']}"
    )
    
    return InterviewAnswerResponse(
        session_id=session_id,
        agent_name=result["agent_name"],
        evaluation=result["evaluation"],
        next_question=result["next_question"],
        suspicion_delta=result["suspicion_delta"],
        authenticity_flags=result["authenticity_flags"]
    )


@router.get("/report/{session_id}", response_model=FinalReportResponse, tags=["interview"])
async def get_final_report(session_id: str):
    """
    Get final evaluation report.
    
    Args:
        session_id: Interview session ID
    
    Returns:
        Final scores, recommendation, and detailed report
    """
    logger.info(f"Generating final report for session {session_id}")
    
    session = get_session(session_id)
    
    # Generate report
    orchestrator = InterviewOrchestrator(session)
    report = orchestrator.generate_final_report()
    
    # Save session
    save_session(session)
    
    # Broadcast to WebSocket
    await broadcast_log(session_id, f"EvaluatorAgent: {report.get('recommendation')}")
    
    return FinalReportResponse(
        session_id=session_id,
        technical_score=report.get("technical_score", 0),
        communication_score=report.get("communication_score", 0),
        cv_authenticity=report.get("cv_authenticity", "Medium"),
        cheating_risk=report.get("cheating_risk", "Low"),
        recommendation=report.get("recommendation", "Manual review required"),
        justification=report.get("justification", ""),
        agent_flags=session.authenticity_flags,
        transcript=session.conversation_transcript
    )


@router.websocket("/ws/{session_id}", name="interview_ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time interview logs.
    
    Broadcasts agent actions and logs to connected clients.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    
    if session_id not in active_connections:
        active_connections[session_id] = []
    
    active_connections[session_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive, receive pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {str(e)}")
    finally:
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]


async def broadcast_log(session_id: str, message: str):
    """Broadcast a log message to all connected WebSocket clients."""
    if session_id not in active_connections:
        return
    
    log_entry = {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "message": message
    }
    
    for connection in active_connections[session_id]:
        try:
            await connection.send_json(log_entry)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {str(e)}")
