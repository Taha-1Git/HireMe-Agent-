"""Unit tests for TrueHire AI backend."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.models.interview import CVProfile, InterviewSession
from app.services.cv_parser import extract_text_from_pdf, parse_cv_with_openai, CVParsingError
from app.services.agents import HRAgent, TechnicalAgent, ProjectDeepDiveAgent, AuthenticityAgent
from app.services.interview import InterviewOrchestrator


class TestCVParsing:
    """Test CV parsing functionality."""
    
    def test_extract_text_from_pdf_invalid_file(self):
        """Test error handling for invalid PDF."""
        with pytest.raises(CVParsingError):
            extract_text_from_pdf(b"not a pdf")
    
    def test_extract_text_from_pdf_empty_file(self):
        """Test error handling for empty file."""
        with pytest.raises(CVParsingError):
            extract_text_from_pdf(b"")
    
    @patch('app.services.cv_parser.client')
    def test_parse_cv_with_openai_success(self, mock_client):
        """Test successful CV parsing with OpenAI."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices[0].message.parsed = CVProfile(
            skills=["Python", "FastAPI"],
            projects=[{"name": "Project1", "description": "Test", "technologies": ["Python"]}],
            education=[{"degree": "BSc", "institution": "University", "field": "CS"}],
            experience=[{"title": "Engineer", "company": "Corp", "duration": "2 years", "description": "Worked on..."}],
            claimed_technologies=["Python", "FastAPI", "React"]
        )
        mock_client.beta.chat.completions.parse.return_value = mock_response
        
        cv_text = "Senior Python Developer with 5 years experience in backend development..."
        result = parse_cv_with_openai(cv_text)
        
        assert result.skills == ["Python", "FastAPI"]
        assert len(result.claimed_technologies) == 3
    
    @patch('app.services.cv_parser.client')
    def test_parse_cv_with_openai_failure(self, mock_client):
        """Test error handling in OpenAI parsing."""
        from openai import BadRequestError
        
        mock_client.beta.chat.completions.parse.side_effect = BadRequestError(
            "Invalid request",
            response=Mock(status_code=400),
            body={}
        )
        
        cv_text = "Some CV text"
        with pytest.raises(CVParsingError):
            parse_cv_with_openai(cv_text)


class TestAgents:
    """Test interview agents."""
    
    @patch('app.services.agents.client')
    def test_hr_agent_question_generation(self, mock_client):
        """Test HR agent generates behavioral question."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "question": "Tell me about a time you led a project.",
            "evaluation_criteria": "Leadership and communication",
            "follow_up_hint": "Team dynamics"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        agent = HRAgent()
        cv_profile = CVProfile(
            skills=["Python"],
            projects=[],
            education=[],
            experience=[],
            claimed_technologies=["Python"]
        )
        
        result = agent.generate_question(cv_profile)
        
        assert "question" in result
        assert "evaluation_criteria" in result
    
    @patch('app.services.agents.client')
    def test_technical_agent_evaluation(self, mock_client):
        """Test technical agent evaluates technical answers."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "depth_assessment": "Good practical knowledge",
            "score": 85,
            "red_flags": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        agent = TechnicalAgent()
        cv_profile = CVProfile(
            skills=["Python", "FastAPI"],
            projects=[],
            education=[],
            experience=[],
            claimed_technologies=["Python", "FastAPI"]
        )
        
        result = agent.evaluate_answer(
            "I used async/await for concurrent request handling",
            "What's your experience with FastAPI?",
            cv_profile
        )
        
        assert "depth_assessment" in result or "score" in result
    
    @patch('app.services.agents.client')
    def test_authenticity_agent_detects_generic_answer(self, mock_client):
        """Test authenticity agent flags generic answers."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "flags": [
                {"type": "generic", "description": "Textbook definition", "severity": "medium"}
            ],
            "authenticity_concern": 0.6,
            "summary": "Answer lacks specific project details"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        agent = AuthenticityAgent()
        cv_profile = CVProfile(
            skills=["Python"],
            projects=[{"name": "ML System", "description": "Recommendation engine", "technologies": ["Python"]}],
            education=[],
            experience=[],
            claimed_technologies=["Python"]
        )
        
        result = agent.analyze_answer(
            "JWT tokens are stored in httpOnly cookies for security",
            cv_profile,
            []
        )
        
        assert "flags" in result
        assert result.get("authenticity_concern", 0) > 0


class TestInterviewOrchestrator:
    """Test interview orchestration."""
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample interview session."""
        cv_profile = CVProfile(
            skills=["Python", "FastAPI", "React"],
            projects=[{"name": "API Server", "description": "REST API", "technologies": ["Python", "FastAPI"]}],
            education=[{"degree": "BSc", "institution": "University", "field": "CS"}],
            experience=[{"title": "Backend Engineer", "company": "Tech Corp", "duration": "3 years", "description": "Developed APIs"}],
            claimed_technologies=["Python", "FastAPI", "React", "PostgreSQL"]
        )
        session = InterviewSession(
            session_id="test-session-123",
            cv_profile=""
        )
        session.set_cv_profile(cv_profile)
        return session
    
    @patch('app.services.agents.client')
    def test_opening_question_generation(self, mock_client, sample_session):
        """Test orchestrator generates opening question."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "question": "Tell me about the API server project you built.",
            "authentication_indicators": "Specific implementation details"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        orchestrator = InterviewOrchestrator(sample_session)
        result = orchestrator.generate_opening_question()
        
        assert "question" in result
        assert result["agent"] in ["technical", "project_deepdive"]
        assert len(sample_session.conversation_transcript) > 0


def test_cv_profile_model():
    """Test CVProfile data model."""
    profile = CVProfile(
        skills=["Python", "SQL"],
        projects=[{"name": "Project1", "description": "Test", "technologies": ["Python"]}],
        education=[{"degree": "BSc", "institution": "Uni", "field": "CS"}],
        experience=[{"title": "Dev", "company": "Corp", "duration": "1 yr", "description": "Dev work"}],
        claimed_technologies=["Python"]
    )
    
    assert len(profile.skills) == 2
    assert len(profile.projects) == 1
    assert profile.claimed_technologies[0] == "Python"


def test_interview_session_model():
    """Test InterviewSession data model."""
    cv_profile = CVProfile(
        skills=["Python"],
        projects=[],
        education=[],
        experience=[],
        claimed_technologies=["Python"]
    )
    
    session = InterviewSession(
        session_id="test-123",
        cv_profile=""
    )
    session.set_cv_profile(cv_profile)
    session.add_message("assistant", "First question", agent="technical")
    
    assert session.get_cv_profile().skills == ["Python"]
    assert len(session.conversation_transcript) == 1
    assert session.conversation_transcript[0]["role"] == "assistant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
