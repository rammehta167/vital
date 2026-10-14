#!/usr/bin/env bash
set -e

echo "===================================================================="
echo " AI Healthcare Companion + Smart Vital Tracker & Emergency System"
echo " B.Tech Final-Year Major Project Prototype"
echo "===================================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please install Python 3.10+."
    exit 1
fi

# Copy .env.example if .env does not exist
if [ ! -f .env ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
fi

# Install dependencies
echo "[INFO] Checking Python dependencies..."
python3 -m pip install -r requirements.txt

# Run seed if database doesn't exist
if [ ! -f backend/app.db ]; then
    echo "[INFO] Database not found. Seeding initial demo data..."
    python3 -m seed.seed
fi

echo ""
echo "===================================================================="
echo " Starting FastAPI Server on http://localhost:8000"
echo " Simulator will auto-start in background."
echo " Press Ctrl+C to stop."
echo "===================================================================="
echo ""

python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
