"""Identity verification API endpoints.

POST /api/identity/verify - Verify identity by comparing two images
GET /api/identity/backend - Get info about which backend is in use (debug)
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.identity import verify_identity, IdentityVerificationError, get_identity_backend_info

logger = logging.getLogger(__name__)

router = APIRouter()


class IdentityVerificationRequest(BaseModel):
    """Request model for identity verification."""
    match_percentage: int
    verified: bool
    status: str


@router.post("/verify", response_model=IdentityVerificationRequest)
async def verify_identity_endpoint(
    reference_image: UploadFile = File(..., description="Reference image (from CV or ID)"),
    live_image: UploadFile = File(..., description="Live snapshot from webcam"),
) -> IdentityVerificationRequest:
    """
    Verify identity by comparing two face images.
    
    Args:
        reference_image: Reference photo from CV, ID card, or student card
        live_image: Live snapshot taken from webcam
        
    Returns:
        IdentityVerificationRequest with:
        - match_percentage: 0-100 similarity score
        - verified: True if match percentage >= 60 (threshold)
        - status: "Verified" or "Mismatch"
        
    Raises:
        400: Invalid files or no faces detected
        500: Verification service error
        
    Example:
        curl -X POST http://localhost:8000/api/identity/verify \\
          -F "reference_image=@id_photo.jpg" \\
          -F "live_image=@webcam_snapshot.jpg"
        
        Response:
        {
          "match_percentage": 85,
          "verified": true,
          "status": "Verified"
        }
    """
    try:
        # Validate files exist and are not empty
        if not reference_image.filename:
            raise HTTPException(
                status_code=400,
                detail="Reference image is required"
            )
        if not live_image.filename:
            raise HTTPException(
                status_code=400,
                detail="Live image is required"
            )
        
        # Read file contents
        ref_content = await reference_image.read()
        live_content = await live_image.read()
        
        if not ref_content:
            raise HTTPException(status_code=400, detail="Reference image is empty")
        if not live_content:
            raise HTTPException(status_code=400, detail="Live image is empty")
        
        # Verify identity (threshold of 0.60 = 60% similarity required)
        # This is conservative: requires >60% match, helps prevent false positives
        match_percentage, verified, status = await verify_identity(
            ref_content,
            live_content,
            threshold=0.60,
        )
        
        logger.info(f"Identity verification result: {status} ({match_percentage}%)")
        
        return IdentityVerificationRequest(
            match_percentage=match_percentage,
            verified=verified,
            status=status,
        )
        
    except IdentityVerificationError as e:
        logger.warning(f"Identity verification failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Identity verification failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in identity verification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Identity verification service error"
        )


@router.get("/backend")
async def get_backend_info() -> dict:
    """
    Get information about which identity verification backend is in use.
    
    Useful for debugging and testing.
    
    Returns:
        Dict with backend name and description
        
    Example:
        {
          "backend": "deepface",
          "description": "DeepFace - Most accurate, uses Facenet512"
        }
    """
    return get_identity_backend_info()
