"""CV upload and management routes."""

import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlmodel import Session, create_engine, SQLSession

from app.core.config import settings
from app.models.interview import InterviewSession, CVUploadResponse
from app.services.cv_parser import parse_cv, CVParsingError

logger = logging.getLogger(__name__)
router = APIRouter()

# Database setup
engine = create_engine(settings.database_url)


@router.post("/upload", response_model=CVUploadResponse, tags=["cv"])
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and parse a CV PDF.
    
    Returns:
        - session_id: Unique interview session ID
        - profile: Parsed CV profile
    
    Raises:
        - 400: Invalid or unsupported file
        - 422: Failed to parse CV
    """
    logger.info(f"CV upload started: {file.filename}")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Read file
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File is too large (max 10MB)")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Parse CV
    try:
        cv_profile = await parse_cv(content)
    except CVParsingError as e:
        logger.error(f"CV parsing error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"CV parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error parsing CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error during CV parsing")
    
    # Create interview session
    session_id = str(uuid.uuid4())
    interview_session = InterviewSession(
        session_id=session_id,
        cv_profile=""  # Will be set below
    )
    interview_session.set_cv_profile(cv_profile)
    
    # Save to database
    try:
        with Session(engine) as db_session:
            db_session.add(interview_session)
            db_session.commit()
            db_session.refresh(interview_session)
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create interview session")
    
    logger.info(f"CV parsed successfully. Session: {session_id}")
    
    return CVUploadResponse(
        session_id=session_id,
        profile=cv_profile,
        message=f"CV parsed successfully. {len(cv_profile.skills)} skills extracted."
    )
