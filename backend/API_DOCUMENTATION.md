"""API Documentation for TrueHire AI Interview Engine"""

# TrueHire AI Interview Engine API

This document describes the API endpoints for CV parsing and AI-powered interview orchestration.

## Overview

The TrueHire AI backend implements a complete interview pipeline:
1. **CV Upload & Parsing** → Extract structured candidate profile
2. **Interview Orchestration** → Five AI agents conduct interview
3. **Real-time Logs** → WebSocket broadcasts agent actions
4. **Final Evaluation** → Automated scoring and recommendation

## Base URL

```
http://localhost:8000
```

## API Endpoints

### 1. Upload & Parse CV

**POST** `/api/cv/upload`

Upload a PDF resume/CV and extract structured profile.

#### Request
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file, required)

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "profile": {
    "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
    "projects": [
      {
        "name": "Recommendation Engine",
        "description": "Collaborative filtering system",
        "technologies": ["Python", "FastAPI", "Redis"]
      }
    ],
    "education": [
      {
        "degree": "BSc",
        "institution": "University Name",
        "field": "Computer Science"
      }
    ],
    "experience": [
      {
        "title": "Senior Backend Engineer",
        "company": "TechCorp",
        "duration": "3 years",
        "description": "Designed scalable APIs..."
      }
    ],
    "claimed_technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"]
  },
  "message": "CV parsed successfully. 4 skills extracted."
}
```

#### Error Responses
- **400**: Invalid file type or corrupted PDF
- **422**: CV parsing failed (no extractable text, etc.)

#### Example Usage
```bash
curl -X POST http://localhost:8000/api/cv/upload \
  -F "file=@resume.pdf"
```

---

### 2. Start Interview

**POST** `/api/interview/start/{session_id}`

Start an interview session with the opening question from an AI agent.

#### Request
- Path: `session_id` (from CV upload response)

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "project_deepdive",
  "opening_question": "You mentioned building a recommendation engine. Walk me through how you handled cold-start recommendations for new users. What challenges came up?",
  "message": "Interview started"
}
```

#### Example Usage
```bash
curl -X POST http://localhost:8000/api/interview/start/550e8400-e29b-41d4-a716-446655440000
```

---

### 3. Submit Answer & Get Next Question

**POST** `/api/interview/answer/{session_id}`

Submit a candidate's answer and receive the next question.

#### Request
```json
{
  "answer": "The cold-start problem was tricky. I solved it using hybrid recommendations. For new users, I'd first recommend popular items from their demographic, then gradually shift to collaborative filtering as more rating data came in. I also built a content-based fallback using item features."
}
```

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_name": "project_deepdive",
  "evaluation": "Strong answer showing deep implementation knowledge. Specific technical tradeoffs mentioned.",
  "next_question": "How did you measure whether the hybrid approach was actually better than pure collaborative filtering?",
  "suspicion_delta": -0.05,
  "authenticity_flags": []
}
```

#### Authenticity Flags Example
```json
{
  "authenticity_flags": [
    {
      "type": "generic",
      "description": "This sounds like a textbook definition rather than specific to your project",
      "severity": "medium"
    },
    {
      "type": "cv_contradiction",
      "description": "CV mentions ML skills but all answers so far focus on frontend",
      "severity": "high"
    }
  ]
}
```

#### Example Usage
```bash
curl -X POST http://localhost:8000/api/interview/answer/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"answer": "The cold-start problem was handled by..."}'
```

---

### 4. Get Final Evaluation Report

**GET** `/api/interview/report/{session_id}`

Generate and retrieve the final evaluation report after interview is complete.

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "technical_score": 87,
  "communication_score": 82,
  "cv_authenticity": "High",
  "cheating_risk": "Low",
  "recommendation": "Shortlist",
  "justification": "Candidate demonstrated strong technical depth and specific project knowledge. Answers were detailed and evidence-based. No red flags detected.",
  "agent_flags": [
    {
      "agent": "AuthenticityAgent",
      "type": "generic",
      "description": "One answer lacked specificity",
      "severity": "low"
    }
  ],
  "transcript": [
    {
      "role": "assistant",
      "content": "You mentioned building a recommendation engine...",
      "agent": "project_deepdive",
      "timestamp": "2024-02-17T10:30:00.000Z"
    },
    {
      "role": "user",
      "content": "The cold-start problem was tricky...",
      "agent": "candidate",
      "timestamp": "2024-02-17T10:31:15.000Z"
    }
  ]
}
```

#### Response Fields

- **technical_score** (0-100): Depth and accuracy of technical knowledge
- **communication_score** (0-100): Clarity and communication ability
- **cv_authenticity** ("High"|"Medium"|"Low"): Whether answers support CV claims
- **cheating_risk** ("Low"|"Medium"|"High"): Likelihood of dishonest answers
- **recommendation** ("Shortlist"|"Manual review required"|"Reject"): Hiring recommendation
- **justification**: Short explanation of recommendation
- **agent_flags**: All authenticity concerns flagged during interview

#### Example Usage
```bash
curl http://localhost:8000/api/interview/report/550e8400-e29b-41d4-a716-446655440000
```

---

### 5. Real-time WebSocket Logs

**WebSocket** `/ws/interview/{session_id}`

Connect to receive real-time agent activity logs during the interview.

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/interview/550e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`${log.timestamp}: ${log.message}`);
  // Output: "2024-02-17T10:30:00.000Z: project_deepdive: Strong project knowledge shown"
};
```

#### Message Format
```json
{
  "timestamp": "2024-02-17T10:30:00.000Z",
  "message": "technical_agent: Good understanding of FastAPI async patterns"
}
```

#### Keep Alive
Send "ping" to keep connection alive:
```javascript
setInterval(() => ws.send('ping'), 30000);
```

---

## The Five AI Agents

### 1. HR Agent
- **Role**: Behavioral and communication assessment
- **Questions**: 1-2 behavioral questions probing teamwork and communication
- **Evaluation**: Communication clarity, interpersonal skills

### 2. Technical Agent
- **Role**: Technical depth and practical knowledge
- **Questions**: Skill-based questions derived from CV technologies
- **Evaluation**: Practical vs. textbook knowledge, problem-solving approach

### 3. Project Deep Dive Agent
- **Role**: Verify project ownership
- **Questions**: Implementation-specific details only project creators would know
- **Evaluation**: Indicators of genuine project experience

### 4. Authenticity Agent
- **Role**: Detect generic or dishonest answers
- **Analysis**: 
  - Generic vs. specific answers (textbook vs. real experience)
  - CV contradictions (claimed skills not reflected in answers)
- **Output**: Flags with severity (low/medium/high)

### 5. Evaluator Agent
- **Role**: Final scoring and recommendation
- **Input**: Full transcript + all agent evaluations + authenticity flags
- **Output**: Technical score, communication score, CV authenticity, cheating risk, recommendation

---

## Testing

### Run Unit Tests
```bash
cd backend
pytest app/tests/test_interview.py -v
```

### Run End-to-End Test (requires OpenAI API key)
```bash
export OPENAI_API_KEY=sk-...
cd backend
python -m pytest app/tests/test_e2e.py::test_interview_flow_e2e -v -s
```

Or run directly:
```bash
python app/tests/test_e2e.py
```

---

## Example Full Interview Flow

```bash
# 1. Upload CV
curl -X POST http://localhost:8000/api/cv/upload \
  -F "file=@sample_cv.pdf"
# Response includes: session_id

SESSION_ID="550e8400-e29b-41d4-a716-446655440000"

# 2. Start interview
curl -X POST http://localhost:8000/api/interview/start/$SESSION_ID

# 3. Submit answers in loop
curl -X POST http://localhost:8000/api/interview/answer/$SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"answer": "First answer..."}'

curl -X POST http://localhost:8000/api/interview/answer/$SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"answer": "Second answer..."}'

# ... continue until interview complete ...

# 4. Get final report
curl http://localhost:8000/api/interview/report/$SESSION_ID
```

---

## Error Handling

All endpoints follow standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid input)
- **404**: Not found (session_id doesn't exist)
- **422**: Unprocessable entity (parsing error)
- **500**: Internal server error

Error response format:
```json
{
  "detail": "Description of what went wrong"
}
```

---

## Interactive Testing via FastAPI Docs

The easiest way to test the API is via the interactive docs:

1. Start the backend: `python app/main.py`
2. Open browser: http://localhost:8000/docs
3. All endpoints are visible with interactive testing interface
4. Click "Try it out" on any endpoint to test

---

## Performance Considerations

- **CV Parsing**: ~5-10 seconds (depends on PDF size and OpenAI response time)
- **Each Answer Processing**: ~3-5 seconds (authenticative + agent evaluation)
- **Final Report**: ~2-3 seconds (evaluator agent synthesis)
- **Total Interview**: ~2-3 minutes for full 5-question session

---

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key (for GPT-4 access)

Optional:
- `DEBUG`: Set to "True" for verbose logging
- `DATABASE_URL`: SQLite path (default: `sqlite:///./truehire.db`)
- `ALLOWED_ORIGINS`: CORS origins (default: `["http://localhost:3000"]`)

---

## Notes on AI Behavior

The agents use GPT-4 with carefully tuned system prompts to:
- Detect generic textbook answers vs. genuine experience
- Flag CV contradictions cautiously (never "proved lying")
- Evaluate technical depth fairly
- Provide actionable hiring recommendations

Prompts are centralized in `app/services/prompts.py` for easy tuning.

