#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check if .env exists, if not warn
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found in root. Backend might miss credentials."
fi

# Export environment variables from .env
export $(grep -v '^#' .env | xargs)

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed (quietly)
echo "📦 Checking dependencies..."
pip install -r railway-api/requirements.txt > /dev/null 2>&1
pip install uvicorn > /dev/null 2>&1

# Set Python path to include root so modules can resolve
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "🚀 Starting GAP Intel Backend API on port 8000..."
echo "✅ API will be available at http://localhost:8000"
echo "📝 Logs will appear below:"
echo "----------------------------------------"

# Run the server using the venv's python
cd railway-api
python3 -m uvicorn server:app --reload --port 8000
