"""End-to-end tests and utilities."""

import json
from pathlib import Path

import fitz  # PyMuPDF


def generate_sample_cv_pdf() -> bytes:
    """
    Generate a sample CV PDF for testing.
    
    Returns:
        PDF file content as bytes
    """
    # Create a new PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # Add CV content
    cv_text = """
ALEX CHEN
alex.chen@email.com | +1-555-0123 | GitHub: github.com/alexchen

PROFESSIONAL SUMMARY
Senior Backend Engineer with 5 years of experience building scalable APIs and microservices
using Python, FastAPI, and cloud technologies. Passionate about clean code and machine learning.

TECHNICAL SKILLS
Languages: Python, JavaScript, SQL
Frameworks: FastAPI, Django, React
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
Tools: Git, Linux, Nginx, Apache Kafka

PROFESSIONAL EXPERIENCE

Senior Backend Engineer | TechCorp Inc. | Jan 2021 - Present
• Designed and implemented real-time recommendation engine using collaborative filtering
  Reduced query time from 500ms to 50ms using Redis caching and algorithm optimization
• Led team of 3 engineers; conducted code reviews and mentored junior developers
• Built microservices architecture with FastAPI; scaled to handle 10k requests/sec
• Implemented JWT authentication and role-based access control across API

Backend Engineer | StartupXYZ | June 2019 - Dec 2020
• Developed REST APIs in Python/FastAPI; achieved 99.9% uptime
• Implemented database migrations and optimization strategies
• Built automated testing suite (pytest); increased coverage from 40% to 92%

Junior Developer | WebAgency | Jan 2019 - May 2019
• Built full-stack features in Django and React
• Created database schemas and wrote complex SQL queries
• Participated in agile development; deployed weekly releases

PROJECTS

Recommendation Engine (Personal)
• Built collaborative filtering recommendation system in Python
• Used NumPy and scikit-learn for ML algorithms
• Implemented Redis caching layer for sub-100ms latency
• Technologies: Python, FastAPI, Redis, PostgreSQL, ML

Real-time Analytics Dashboard
• Created live data visualization dashboard at TechCorp
• Streamed data via WebSockets to React frontend
• Handled 1M+ events per day using message queue (Kafka)
• Technologies: Python, WebSockets, Kafka, React, PostgreSQL

EDUCATION
B.S. in Computer Science | State University | May 2019
GPA: 3.7/4.0

CERTIFICATIONS
• AWS Solutions Architect Associate (2022)
• MongoDB Certified Associate Developer (2021)
"""
    
    # Insert text into PDF
    text_rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(text_rect, cv_text, fontsize=10, fontname="helv")
    
    # Save to bytes
    pdf_bytes = doc.write()
    doc.close()
    
    return pdf_bytes


def test_interview_flow_e2e():
    """
    End-to-end test of CV parsing and interview flow.
    
    This test uses the REAL OpenAI API and should only be run manually
    with a valid OPENAI_API_KEY environment variable.
    
    Run with: pytest app/tests/test_e2e.py::test_interview_flow_e2e -v -s
    """
    import asyncio
    from app.services.cv_parser import parse_cv
    from app.models.interview import InterviewSession
    from app.services.interview import InterviewOrchestrator
    
    print("\n" + "="*80)
    print("END-TO-END INTERVIEW TEST")
    print("="*80)
    
    # Generate sample CV
    print("\n1. Generating sample CV PDF...")
    pdf_bytes = generate_sample_cv_pdf()
    print(f"   PDF generated: {len(pdf_bytes)} bytes")
    
    # Parse CV
    print("\n2. Parsing CV with OpenAI...")
    try:
        cv_profile = asyncio.run(parse_cv(pdf_bytes))
        print(f"   ✓ CV parsed successfully")
        print(f"   - Skills: {', '.join(cv_profile.skills[:5])}")
        print(f"   - Technologies: {', '.join(cv_profile.claimed_technologies)}")
        print(f"   - Projects: {len(cv_profile.projects)} found")
        print(f"   - Experience: {len(cv_profile.experience)} roles")
    except Exception as e:
        print(f"   ✗ CV parsing failed: {str(e)}")
        return
    
    # Create interview session
    print("\n3. Creating interview session...")
    session = InterviewSession(session_id="e2e-test-1", cv_profile="")
    session.set_cv_profile(cv_profile)
    
    # Start interview
    print("\n4. Starting interview...")
    orchestrator = InterviewOrchestrator(session)
    
    try:
        opening = orchestrator.generate_opening_question()
        print(f"   Agent: {opening['agent']}")
        print(f"   Question: {opening['question']}")
    except Exception as e:
        print(f"   ✗ Failed to generate opening question: {str(e)}")
        return
    
    # Simulate answers and continue interview
    print("\n5. Simulating interview answers...")
    
    sample_answers = [
        """The recommendation engine was the most complex project. I used collaborative filtering
        to predict which products users would like. The main challenge was handling cold-start 
        users who had no history. I solved it by using content-based filtering as a fallback,
        then gradually transitioned to collaborative filtering as more data came in. I implemented
        it in Python using NumPy and scikit-learn, with Redis for caching predictions.""",
        
        """I'd say my strongest area is backend API design. I focus on clean architecture,
        proper separation of concerns, and building systems that scale. In my current role at TechCorp,
        I redesigned our entire API from a monolith to microservices using FastAPI, which let us
        scale each service independently. We went from handling 1k req/sec to 10k req/sec.""",
        
        """When explaining technical concepts, I try to use concrete examples from my own work.
        For instance, when discussing authentication, I'd explain that we chose JWT with httpOnly
        cookies instead of localStorage because we discovered localStorage was vulnerable to XSS attacks
        in a previous project. It's important to share real lessons learned."""
    ]
    
    for i, answer in enumerate(sample_answers, 1):
        try:
            result = orchestrator.process_answer(answer)
            print(f"\n   Answer {i}:")
            print(f"   - Agent: {result['agent_name']}")
            print(f"   - Evaluation: {result['evaluation'][:100]}...")
            print(f"   - Suspicion delta: {result['suspicion_delta']:.2f}")
            if result['authenticity_flags']:
                print(f"   - Flags: {len(result['authenticity_flags'])} authenticity concerns")
        except Exception as e:
            print(f"   ✗ Error processing answer {i}: {str(e)}")
            break
    
    # Generate final report
    print("\n6. Generating final evaluation report...")
    try:
        report = orchestrator.generate_final_report()
        
        print(f"\n   FINAL REPORT")
        print(f"   " + "="*50)
        print(f"   Technical Score: {report.get('technical_score', '?')}/100")
        print(f"   Communication Score: {report.get('communication_score', '?')}/100")
        print(f"   CV Authenticity: {report.get('cv_authenticity', '?')}")
        print(f"   Cheating Risk: {report.get('cheating_risk', '?')}")
        print(f"   Recommendation: {report.get('recommendation', '?')}")
        print(f"   Justification: {report.get('justification', '?')}")
        
        print(f"\n   Key Strengths:")
        for strength in report.get('key_strengths', []):
            print(f"   ✓ {strength}")
        
        print(f"\n   Concerns:")
        for concern in report.get('concerns', []):
            print(f"   ⚠ {concern}")
    
    except Exception as e:
        print(f"   ✗ Failed to generate report: {str(e)}")
        return
    
    print("\n" + "="*80)
    print("✓ END-TO-END TEST COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")
    
    return {
        "cv_profile": cv_profile.model_dump(),
        "interview_transcript": session.conversation_transcript,
        "final_report": report,
        "authenticity_flags": session.authenticity_flags
    }


if __name__ == "__main__":
    # Run the end-to-end test
    import os
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=sk-...")
        exit(1)
    
    result = test_interview_flow_e2e()
    
    # Save results to file for review
    if result:
        output_file = "e2e_test_results.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Results saved to {output_file}")
