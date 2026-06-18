"""Interview orchestration service."""

import json
import logging
from typing import Optional
from datetime import datetime

from app.models.interview import InterviewSession, CVProfile
from app.services.agents import (
    HRAgent, TechnicalAgent, ProjectDeepDiveAgent,
    AuthenticityAgent, EvaluatorAgent
)

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """Orchestrates the interview flow with five agents."""
    
    def __init__(self, session: InterviewSession):
        self.session = session
        self.cv_profile = session.get_cv_profile()
        self.hr_agent = HRAgent()
        self.technical_agent = TechnicalAgent()
        self.deepdive_agent = ProjectDeepDiveAgent()
        self.authenticity_agent = AuthenticityAgent()
        self.evaluator_agent = EvaluatorAgent()
        
        # State tracking
        self.agent_queue = ["technical", "hr", "deepdive", "technical", "hr"]  # 5 agents, can repeat
        self.current_agent_index = 0
        self.questions_asked = 0
        self.max_questions = 10
    
    def generate_opening_question(self) -> dict:
        """Generate the first question from Technical or ProjectDeepDive."""
        logger.info(f"Generating opening question for session {self.session.session_id}")
        
        if self.cv_profile.projects:
            # Start with project deep dive
            agent_name = "project_deepdive"
            project = self.deepdive_agent.select_project(self.cv_profile)
            question_obj = self.deepdive_agent.generate_question(project, self.cv_profile)
        else:
            # Fall back to technical
            agent_name = "technical"
            question_obj = self.technical_agent.generate_question(self.cv_profile)
        
        question = question_obj.get("question", "Tell me about your experience.")
        
        # Store in session
        self.session.add_message("assistant", question, agent=agent_name)
        self.session.current_agent = agent_name
        self.questions_asked += 1
        
        return {
            "agent": agent_name,
            "question": question,
            "question_object": question_obj
        }
    
    def process_answer(self, candidate_answer: str) -> dict:
        """
        Process candidate's answer, run through agents, determine next question.
        
        Returns:
            {
                "agent_name": str,
                "evaluation": str,
                "next_question": str,
                "suspicion_delta": float,
                "authenticity_flags": list
            }
        """
        logger.info(f"Processing answer for session {self.session.session_id}")
        
        # Store candidate's answer
        self.session.add_message("user", candidate_answer, agent="candidate")
        
        # Run through authenticity agent
        authenticity_result = self.authenticity_agent.analyze_answer(
            candidate_answer, self.cv_profile, self.session.conversation_transcript
        )
        
        flags = authenticity_result.get("flags", [])
        authenticity_concern = authenticity_result.get("authenticity_concern", 0.0)
        
        # Update suspicion score
        suspicion_delta = authenticity_concern * 0.2  # Scale to reasonable bounds
        self.session.suspicion_score += suspicion_delta
        
        # Store flags
        for flag in flags:
            self.session.authenticity_flags.append({
                "agent": "AuthenticityAgent",
                **flag
            })
        
        # Evaluate with current agent
        current_agent_name = self.session.current_agent or "technical"
        evaluation = ""
        
        if current_agent_name == "technical":
            eval_result = self.technical_agent.evaluate_answer(
                candidate_answer, 
                self.session.conversation_transcript[-2]["content"],  # Previous question
                self.cv_profile
            )
            evaluation = eval_result.get("evaluation", "")
        elif current_agent_name == "hr":
            eval_result = self.hr_agent.evaluate_answer(candidate_answer, self.cv_profile)
            evaluation = eval_result.get("evaluation", "")
        elif current_agent_name == "project_deepdive":
            project = self.deepdive_agent.select_project(self.cv_profile)
            if project:
                eval_result = self.deepdive_agent.evaluate_answer(candidate_answer, project)
                evaluation = eval_result.get("evaluation", "")
        
        # Store evaluation
        if evaluation:
            self.session.add_message("system", evaluation, agent=f"{current_agent_name}_evaluation")
        
        # Determine next question
        self.current_agent_index = (self.current_agent_index + 1) % len(self.agent_queue)
        next_agent_name = self.agent_queue[self.current_agent_index]
        
        # Generate next question
        if self.questions_asked < self.max_questions:
            if next_agent_name == "technical":
                next_q_obj = self.technical_agent.generate_question(
                    self.cv_profile, 
                    previous_answer=candidate_answer if authenticity_concern > 0.5 else None
                )
                next_question = next_q_obj.get("question", "")
            elif next_agent_name == "hr":
                next_q_obj = self.hr_agent.generate_question(
                    self.cv_profile,
                    session_context=f"Last answer quality: {authenticity_concern}"
                )
                next_question = next_q_obj.get("question", "")
            elif next_agent_name == "project_deepdive":
                project = self.deepdive_agent.select_project(self.cv_profile)
                if project:
                    next_q_obj = self.deepdive_agent.generate_question(project, self.cv_profile)
                    next_question = next_q_obj.get("question", "")
                else:
                    # Fall back to technical
                    next_agent_name = "technical"
                    next_q_obj = self.technical_agent.generate_question(self.cv_profile)
                    next_question = next_q_obj.get("question", "")
            else:
                next_question = "Interview complete."
        else:
            next_question = "Interview complete."
        
        # Store next question
        if next_question != "Interview complete.":
            self.session.add_message("assistant", next_question, agent=next_agent_name)
            self.session.current_agent = next_agent_name
        else:
            self.session.completed = True
        
        self.questions_asked += 1
        
        return {
            "agent_name": current_agent_name,
            "evaluation": evaluation,
            "next_question": next_question,
            "suspicion_delta": suspicion_delta,
            "authenticity_flags": flags
        }
    
    def generate_final_report(self) -> dict:
        """Generate final evaluation report."""
        logger.info(f"Generating final report for session {self.session.session_id}")
        
        report = self.evaluator_agent.generate_report(
            self.cv_profile,
            self.session.conversation_transcript,
            self.session.authenticity_flags
        )
        
        # Store report
        self.session.final_report = json.dumps(report)
        self.session.completed = True
        
        return report
