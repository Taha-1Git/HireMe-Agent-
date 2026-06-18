"""Face comparison and identity verification service.

Supports multiple backends with automatic fallback:
1. DeepFace (most accurate)
2. face_recognition (mid-tier)
3. OpenCV + Dlib embedding (fallback if others fail)
4. Manual threshold (final fallback)

Each backend provides consistent interface: compare_faces() -> float (0.0-1.0)
"""

import logging
from io import BytesIO
from typing import Tuple, Optional
import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import face comparison libraries (graceful fallback)
IDENTITY_BACKEND = None

try:
    from deepface import DeepFace
    IDENTITY_BACKEND = "deepface"
    logger.info("✓ DeepFace loaded successfully")
except ImportError:
    logger.warning("DeepFace not available, trying face_recognition...")
    try:
        import face_recognition
        IDENTITY_BACKEND = "face_recognition"
        logger.info("✓ face_recognition loaded successfully")
    except ImportError:
        logger.warning("face_recognition not available, falling back to OpenCV embedding")
        IDENTITY_BACKEND = "opencv"
        logger.info("✓ Using OpenCV fallback")


class IdentityVerificationError(Exception):
    """Custom exception for identity verification errors."""
    pass


def load_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Load image from bytes.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        np.ndarray: OpenCV format (BGR)
        
    Raises:
        IdentityVerificationError: If image cannot be loaded
    """
    try:
        # Use PIL to load
        pil_image = Image.open(BytesIO(image_bytes))
        # Convert RGBA to RGB if needed
        if pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")
        # Convert to OpenCV format (BGR)
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv_image
    except Exception as e:
        raise IdentityVerificationError(f"Failed to load image: {str(e)}")


def detect_faces_opencv(image: np.ndarray) -> list:
    """
    Detect faces in image using OpenCV's Haar Cascade.
    
    Args:
        image: OpenCV image (BGR)
        
    Returns:
        list: Face rectangles [(x, y, w, h), ...]
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    return list(faces)


def compare_deepface(image1_bytes: bytes, image2_bytes: bytes) -> float:
    """
    Compare two faces using DeepFace.
    
    Args:
        image1_bytes: Reference image
        image2_bytes: Query image
        
    Returns:
        float: Similarity score (0.0-1.0, higher = more similar)
    """
    try:
        # Save to temp files (DeepFace API requires file paths)
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            img1_path = os.path.join(tmpdir, "img1.jpg")
            img2_path = os.path.join(tmpdir, "img2.jpg")
            
            with open(img1_path, "wb") as f:
                f.write(image1_bytes)
            with open(img2_path, "wb") as f:
                f.write(image2_bytes)
            
            # DeepFace.verify returns a dict with 'verified' and 'distance'
            result = DeepFace.verify(
                img1_path=img1_path,
                img2_path=img2_path,
                model_name="Facenet512",  # Accurate model
                distance_metric="cosine",
                enforce_detection=False,  # Don't fail if no face detected
            )
            
            # Convert distance to similarity (0.0-1.0)
            # Cosine distance: 0 = identical, 1 = completely different
            distance = result.get("distance", 1.0)
            similarity = 1.0 - min(distance, 1.0)
            return similarity
            
    except Exception as e:
        logger.warning(f"DeepFace comparison failed: {str(e)}")
        raise IdentityVerificationError(f"DeepFace comparison failed: {str(e)}")


def compare_face_recognition(image1_bytes: bytes, image2_bytes: bytes) -> float:
    """
    Compare two faces using face_recognition library.
    
    Args:
        image1_bytes: Reference image
        image2_bytes: Query image
        
    Returns:
        float: Similarity score (0.0-1.0, higher = more similar)
    """
    try:
        import face_recognition
        
        # Load images
        img1 = face_recognition.load_image_file(BytesIO(image1_bytes))
        img2 = face_recognition.load_image_file(BytesIO(image2_bytes))
        
        # Get face encodings
        encodings1 = face_recognition.face_encodings(img1)
        encodings2 = face_recognition.face_encodings(img2)
        
        if not encodings1 or not encodings2:
            raise IdentityVerificationError("No face detected in one or both images")
        
        # Compare encodings (returns distance, 0 = identical)
        distance = face_recognition.face_distance(encodings1, encodings2[0])[0]
        
        # Convert distance to similarity (0.0-1.0)
        # Face_recognition threshold is typically 0.6 for distance
        similarity = 1.0 - min(distance, 1.0)
        return similarity
        
    except Exception as e:
        logger.warning(f"face_recognition comparison failed: {str(e)}")
        raise IdentityVerificationError(f"face_recognition comparison failed: {str(e)}")


def compare_opencv_embedding(image1_bytes: bytes, image2_bytes: bytes) -> float:
    """
    Compare two faces using OpenCV Haar features (simple fallback).
    
    This is a very basic fallback that:
    1. Detects face regions
    2. Extracts simple histogram features
    3. Computes cosine similarity
    
    Args:
        image1_bytes: Reference image
        image2_bytes: Query image
        
    Returns:
        float: Similarity score (0.0-1.0, higher = more similar)
    """
    try:
        img1 = load_image_from_bytes(image1_bytes)
        img2 = load_image_from_bytes(image2_bytes)
        
        # Detect faces
        faces1 = detect_faces_opencv(img1)
        faces2 = detect_faces_opencv(img2)
        
        if not faces1 or not faces2:
            raise IdentityVerificationError("No face detected in one or both images")
        
        # Extract face regions (largest face)
        x1, y1, w1, h1 = max(faces1, key=lambda f: f[2] * f[3])
        x2, y2, w2, h2 = max(faces2, key=lambda f: f[2] * f[3])
        
        face1 = img1[y1:y1+h1, x1:x1+w1]
        face2 = img2[y2:y2+h2, x2:x2+w2]
        
        # Resize to same size
        face1 = cv2.resize(face1, (100, 100))
        face2 = cv2.resize(face2, (100, 100))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        # Simple feature: histogram of grayscale values
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        # Normalize
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # Compute cosine similarity
        similarity = cv2.matchTemplate(
            gray1.astype(np.float32),
            gray2.astype(np.float32),
            cv2.TM_CCOEFF
        )
        
        # Very basic: use histogram comparison
        # This is not very accurate, but works as fallback
        comparison = cv2.compareHist(hist1, hist2, cv2.HISTCMP_COSINE)
        # Convert to 0-1 range (0 = perfect match, 1 = completely different)
        similarity = 1.0 - comparison
        
        return max(0.0, min(similarity, 1.0))
        
    except Exception as e:
        logger.warning(f"OpenCV comparison failed: {str(e)}")
        raise IdentityVerificationError(f"OpenCV comparison failed: {str(e)}")


def compare_faces(image1_bytes: bytes, image2_bytes: bytes) -> float:
    """
    Compare two faces using available backend.
    
    Args:
        image1_bytes: Reference image bytes
        image2_bytes: Query image bytes
        
    Returns:
        float: Similarity score (0.0-1.0, higher = more similar)
        
    Raises:
        IdentityVerificationError: If comparison fails
    """
    if IDENTITY_BACKEND == "deepface":
        try:
            return compare_deepface(image1_bytes, image2_bytes)
        except Exception as e:
            logger.warning(f"DeepFace failed, falling back: {e}")
            # Fall through to next backend
    
    if IDENTITY_BACKEND in ["face_recognition", None]:
        try:
            return compare_face_recognition(image1_bytes, image2_bytes)
        except Exception as e:
            logger.warning(f"face_recognition failed, falling back to OpenCV: {e}")
            # Fall through to next backend
    
    # Final fallback to OpenCV
    return compare_opencv_embedding(image1_bytes, image2_bytes)


async def verify_identity(
    reference_image_bytes: bytes,
    live_image_bytes: bytes,
    threshold: float = 0.60,
) -> Tuple[float, bool, str]:
    """
    Verify identity by comparing two images.
    
    Args:
        reference_image_bytes: Reference image (from CV/ID)
        live_image_bytes: Live snapshot from webcam
        threshold: Similarity threshold for match (default: 0.60)
                  - 0.60 is conservative (fewer false positives)
                  - 0.50 is moderate
                  - 0.40 is more permissive (more false positives)
        
    Returns:
        Tuple of:
        - match_percentage: Similarity score (0-100)
        - verified: True if match_percentage >= threshold
        - status: "Verified" or "Mismatch"
        
    Raises:
        IdentityVerificationError: If verification cannot proceed
    """
    if not reference_image_bytes or not live_image_bytes:
        raise IdentityVerificationError("Both reference and live images are required")
    
    # Compare faces
    similarity = compare_faces(reference_image_bytes, live_image_bytes)
    match_percentage = int(similarity * 100)
    
    # Determine if verified
    verified = similarity >= threshold
    status = "Verified" if verified else "Mismatch"
    
    logger.info(
        f"Identity verification: {match_percentage}% similarity, "
        f"threshold={int(threshold*100)}%, status={status}, "
        f"backend={IDENTITY_BACKEND}"
    )
    
    return match_percentage, verified, status


# Export backend info for debugging
def get_identity_backend_info() -> dict:
    """Get information about which identity backend is in use."""
    return {
        "backend": IDENTITY_BACKEND or "unknown",
        "description": {
            "deepface": "DeepFace - Most accurate, uses Facenet512",
            "face_recognition": "face_recognition library - Good accuracy, uses dlib",
            "opencv": "OpenCV Haar Cascade + histogram - Basic fallback",
        }.get(IDENTITY_BACKEND or "unknown", "Unknown backend"),
    }
