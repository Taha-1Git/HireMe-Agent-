#!/bin/bash
# Quick reference for running the interview engine

echo "🚀 TrueHire AI Interview Engine — Quick Start"
echo "=============================================="
echo ""

# Check if .env has API key
if grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "✓ OpenAI API key configured"
else
    echo "⚠️  WARNING: OPENAI_API_KEY not set in .env"
    echo "   Set it with: echo 'OPENAI_API_KEY=sk-...' >> .env"
fi

echo ""
echo "📚 API Endpoints:"
echo "  POST   /api/cv/upload              - Upload and parse CV"
echo "  POST   /api/interview/start/{id}   - Start interview"
echo "  POST   /api/interview/answer/{id}  - Submit answer"
echo "  GET    /api/interview/report/{id}  - Get final report"
echo "  WS     /ws/interview/{id}          - Real-time logs"
echo ""

echo "🧪 Testing:"
echo "  pytest app/tests/test_interview.py -v          # Unit tests"
echo "  python app/tests/test_e2e.py                   # Full end-to-end"
echo ""

echo "📖 Documentation:"
echo "  - API_DOCUMENTATION.md          - Complete API reference"
echo "  - IMPLEMENTATION_SUMMARY.md     - What was built"
echo ""

echo "🔗 Interactive Testing:"
echo "  1. Start: python app/main.py"
echo "  2. Open: http://localhost:8000/docs"
echo "  3. Try endpoints in the interactive Swagger UI"
echo ""
