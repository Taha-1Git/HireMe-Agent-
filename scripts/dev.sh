#!/bin/bash

# TrueHire AI Development Script
# Starts both frontend and backend servers

set -e

echo "🚀 Starting TrueHire AI development servers..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Start backend in background
echo -e "${BLUE}📦 Starting backend (FastAPI)...${NC}"
cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Creating it now..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

python app/main.py &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo -e "${BLUE}⚛️  Starting frontend (Next.js)...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "⚠️  Dependencies not found. Installing with pnpm..."
    pnpm install
fi

pnpm dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Both servers are running!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Frontend:  http://localhost:3000"
echo "📍 Backend:   http://localhost:8000"
echo "📍 Health:    http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop both servers..."
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
