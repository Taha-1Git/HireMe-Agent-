"""CV parsing service using OpenAI with structured outputs."""

import json
import logging
from io import BytesIO
import fitz  # PyMuPDF

from openai import OpenAI, BadRequestError
from app.models.interview import CVProfile
from app.services.prompts import CV_PARSING_PROMPT

logger = logging.getLogger(__name__)

client = OpenAI()


class CVParsingError(Exception):
    """Custom exception for CV parsing failures."""
    pass


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 10) -> str:
    """
    Extract text from PDF bytes.
    
    Args:
        pdf_bytes: PDF file content as bytes
        max_pages: Maximum pages to extract (to prevent huge documents)
    
    Returns:
        Extracted text
    
    Raises:
        CVParsingError: If PDF is invalid or has no extractable text
    """
    try:
        pdf_stream = BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        if doc.page_count == 0:
            raise CVParsingError("PDF has no pages")
        
        text = ""
        for page_num in range(min(doc.page_count, max_pages)):
            page = doc[page_num]
            text += page.get_text()
        
        doc.close()
        
        if not text.strip():
            raise CVParsingError("PDF contains no extractable text. Is it scanned or image-only?")
        
        return text.strip()
    
    except fitz.FileError:
        raise CVParsingError("Invalid or corrupted PDF file")
    except Exception as e:
        raise CVParsingError(f"Error reading PDF: {str(e)}")


def parse_cv_with_openai(cv_text: str) -> CVProfile:
    """
    Parse CV text using OpenAI's structured output (JSON mode).
    
    Args:
        cv_text: Raw CV text extracted from PDF
    
    Returns:
        CVProfile with structured data
    
    Raises:
        CVParsingError: If parsing fails or JSON is invalid
    """
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": CV_PARSING_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Extract CV information:\n\n{cv_text}"
                }
            ],
            response_format=CVProfile,
            temperature=0.1,  # Low temperature for consistency
        )
        
        # Extract parsed object
        parsed = response.choices[0].message.parsed
        
        if not parsed:
            raise CVParsingError("OpenAI returned empty response")
        
        return parsed
    
    except BadRequestError as e:
        raise CVParsingError(f"OpenAI API error: {str(e)}")
    except json.JSONDecodeError as e:
        raise CVParsingError(f"Invalid JSON response from OpenAI: {str(e)}")
    except Exception as e:
        raise CVParsingError(f"Error parsing CV with OpenAI: {str(e)}")


async def parse_cv(pdf_bytes: bytes) -> CVProfile:
    """
    Main CV parsing pipeline: extract text -> call OpenAI -> return structured profile.
    
    Args:
        pdf_bytes: PDF file content
    
    Returns:
        Parsed CVProfile
    
    Raises:
        CVParsingError: If any step fails
    """
    # Step 1: Extract text from PDF
    logger.info("Extracting text from PDF...")
    cv_text = extract_text_from_pdf(pdf_bytes)
    
    if len(cv_text) < 50:
        raise CVParsingError("PDF text is too short to be a valid CV")
    
    logger.info(f"Extracted {len(cv_text)} characters from PDF")
    
    # Step 2: Parse with OpenAI
    logger.info("Parsing CV with OpenAI...")
    profile = parse_cv_with_openai(cv_text)
    
    logger.info(f"CV parsed successfully: {len(profile.skills)} skills, {len(profile.projects)} projects")
    
    return profile
