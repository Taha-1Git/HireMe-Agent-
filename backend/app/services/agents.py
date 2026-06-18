"""Interview agents for TrueHire AI."""

import json
import logging
from typing import Optional

from openai import OpenAI

from app.models.interview import InterviewSession, CVProfile
from app.services.prompts import (
    HR_AGENT_PROMPT,
    TECHNICAL_AGENT_PROMPT,
    PROJECT_DEEPDIVE_AGENT_PROMPT,
    AUTHENTICITY_AGENT_PROMPT,
    EVALUATOR_AGENT_PROMPT
)

logger = logging.getLogger(__name__)
client = OpenAI()


class Agent:
    """Base agent class."""
    
    name: str
    system_prompt: str
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    def _call_openai(self, user_message: str, json_mode: bool = False) -> str:
        """Call OpenAI API."""
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7 if not json_mode else 0.1,
                response_format={"type": "json_object"} if json_mode else None,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error in {self.name}: {str(e)}")
            raise


class HRAgent(Agent):
    """HR Agent: behavioral and communication assessment."""
    
    system_prompt = HR_AGENT_PROMPT
    
    def generate_question(self, cv_profile: CVProfile, session_context: Optional[str] = None) -> dict:
        """Generate a behavioral question."""
        context = f"\nPrevious context: {session_context}" if session_context else ""
        message = f"Generate a behavioral question for a candidate with this profile:\n{cv_profile.model_dump_json()}{context}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)
    
    def evaluate_answer(self, answer: str, cv_profile: CVProfile) -> dict:
        """Evaluate a candidate's behavioral answer."""
        message = f"Evaluate this answer for communication clarity and teamwork:\n\nAnswer: {answer}\n\nCandidate profile: {cv_profile.model_dump_json()}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)


class TechnicalAgent(Agent):
    """Technical Agent: skill and knowledge assessment."""
    
    system_prompt = TECHNICAL_AGENT_PROMPT
    
    def generate_question(self, cv_profile: CVProfile, previous_answer: Optional[str] = None) -> dict:
        """Generate a technical question based on CV technologies."""
        if not cv_profile.claimed_technologies:
            return {
                "question": "What programming languages are you most experienced with?",
                "claimed_technology": "General",
                "expected_depth": "Practical experience with real-world applications"
            }
        
        context = f"\n\nPrevious answer: {previous_answer}\n(Generate a follow-up or deeper question if answer was weak)" if previous_answer else ""
        message = f"Generate a technical question for a candidate with these skills:\n{json.dumps(cv_profile.claimed_technologies)}\n\nProfile: {cv_profile.model_dump_json()}{context}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)
    
    def evaluate_answer(self, answer: str, question: str, cv_profile: CVProfile) -> dict:
        """Evaluate technical depth of answer."""
        message = f"Evaluate the technical depth and accuracy of this answer:\n\nQuestion: {question}\nAnswer: {answer}\n\nCandidate skills: {json.dumps(cv_profile.claimed_technologies)}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)


class ProjectDeepDiveAgent(Agent):
    """Project Deep Dive Agent: verify project claims."""
    
    system_prompt = PROJECT_DEEPDIVE_AGENT_PROMPT
    
    def select_project(self, cv_profile: CVProfile) -> Optional[dict]:
        """Select a project to deep-dive on."""
        if not cv_profile.projects:
            return None
        return cv_profile.projects[0]  # For now, always first project
    
    def generate_question(self, project: dict, cv_profile: CVProfile) -> dict:
        """Generate implementation-detail question about a project."""
        message = f"Generate a deep-dive question about this project that only the person who built it would answer correctly:\n\nProject: {json.dumps(project)}\n\nFull profile: {cv_profile.model_dump_json()}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)
    
    def evaluate_answer(self, answer: str, project: dict) -> dict:
        """Evaluate if answer indicates genuine project ownership."""
        message = f"Does this answer indicate the candidate actually built this project? Look for specific technical details.\n\nProject: {json.dumps(project)}\n\nAnswer: {answer}"
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)


class AuthenticityAgent(Agent):
    """Authenticity Agent: detect generic vs. specific answers and CV contradictions."""
    
    system_prompt = AUTHENTICITY_AGENT_PROMPT
    
    def analyze_answer(self, answer: str, cv_profile: CVProfile, transcript: list[dict]) -> dict:
        """Analyze answer for authenticity red flags."""
        transcript_text = "\n".join([f"{msg.get('agent') or msg.get('role', 'User')}: {msg.get('content') or ''}" for msg in transcript[-10:]])  # Last 10 messages
        
        message = f"""Review this answer for authenticity concerns:

CV Profile:
{cv_profile.model_dump_json()}

Interview Transcript (recent):
{transcript_text}

Latest Answer:
{answer}

Identify:
1. If this is a generic textbook answer or specific to their experience
2. Any contradictions with their CV claims"""
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)


class EvaluatorAgent(Agent):
    """Evaluator Agent: final scoring and recommendation."""
    
    system_prompt = EVALUATOR_AGENT_PROMPT
    
    def generate_report(self, cv_profile: CVProfile, transcript: list[dict], authenticity_flags: list[dict]) -> dict:
        """Generate final evaluation report."""
        transcript_text = "\n".join([f"{msg.get('agent', 'User')}: {msg.get('content', '')}" for msg in transcript])
        
        message = f"""Generate a final hiring evaluation based on this interview:

CV Profile:
{cv_profile.model_dump_json()}

Full Interview Transcript:
{transcript_text}

Authenticity Flags Raised:
{json.dumps(authenticity_flags, indent=2)}

Provide final scores and recommendation."""
        
        response = self._call_openai(message, json_mode=True)
        return json.loads(response)
