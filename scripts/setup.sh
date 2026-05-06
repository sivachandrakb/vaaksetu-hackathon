#!/bin/bash
# VaakSetu — Development Setup Script
set -e

echo "🎙️  VaakSetu Setup"
echo "=================="

# Check Python
python3 --version || { echo "Python 3.10+ required"; exit 1; }

# Check Node
node --version || { echo "Node 18+ required"; exit 1; }

# Copy env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env — please fill in your OPENAI_API_KEY"
fi

echo ""
echo "── Backend Setup ─────────────────────────────────"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend dependencies installed"
cd ..

echo ""
echo "── Frontend Setup ────────────────────────────────"
cd frontend
npm install
echo "✅ Frontend dependencies installed"
cd ..

echo ""
echo "── Done! ─────────────────────────────────────────"
echo ""
echo "To run the backend:"
echo "  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "To run the frontend (separate terminal):"
echo "  cd frontend && npm run dev"
echo ""
echo "Or use Docker:"
echo "  docker-compose -f docker/docker-compose.yml up --build"
echo ""
echo "Frontend → http://localhost:3000"
echo "API Docs → http://localhost:8000/docs"
