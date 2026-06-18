# TrueHire AI — Live Demo Script (3-5 Minutes)

### 1. The Hook (30s)
- **Visual**: Landing Page (`/`)
- **Narrative**: "In a world of remote hiring and deepfakes, how do you verify who someone is and if they actually built what they claim? TrueHire AI is a biometric-verified interview platform."

### 2. Onboarding (60s)
- **Action**: Click 'Start Verification Flow'. Upload `Alex_Chen_CV.pdf`.
- **Action**: Identity Verification. Capture webcam snapshot vs CV photo.
- **Action**: Liveness Check. Follow instruction (e.g., "Blink twice").
- **Narrative**: "We aren't just taking photos; we're running browser-side liveness detection to ensure a real human presence."

### 3. The Interview (90s)
- **Action**: Interview starts. Agent asks about the "Recommendation Engine".
- **Action**: Answer genuinely. Watch the 'Agent Console' log real-time evaluation.
- **Action**: **WOW MOMENT 1**: Look away from screen or have a friend peek into the frame. Observe the 'Pulse Perimeter' glow Amber and the 'Risk Score' rise.
- **Action**: **WOW MOMENT 2**: Click 'Simulate: Contradiction'. Observe the Authenticity Agent flagging the mismatch between the answer and CV claims.

### 4. The Report (30s)
- **Action**: Click 'End Session & Review'.
- **Narrative**: "TrueHire synthesizes all data into a final recommendation. We see technical depth, communication scores, and an 'Authenticity Profile' that flags risks for manual review."

### 5. Summary
- Fully working: Biometric monitoring, CV Parsing, Multi-agent orchestration, Demo triggers.
- Run with: `scripts/dev.sh` (or `dev.ps1`). Ensure `OPENAI_API_KEY` is set in `backend/.env`.