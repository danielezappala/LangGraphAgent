#!/bin/bash

# Function to clean up child processes on exit
cleanup() {
    echo "Stopping child processes..."
    # Send SIGTERM to all processes in the current process group
    pkill -P $$
    wait
    echo "All processes stopped."
}

# Set a trap to run the cleanup function on script exit
trap cleanup EXIT

# Check if the virtual environment directory exists
if [ ! -d "venv" ]; then
    echo "Virtual environment 'venv' not found. Please run the setup script first."
    exit 1
fi

# Check if the frontend node_modules directory exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Frontend dependencies 'node_modules' not found. Please run the setup script first."
    exit 1
fi

# Activate Python virtual environment
source venv/bin/activate

# Set PYTHONPATH to the project root directory to ensure correct module resolution
export PYTHONPATH=$(pwd)

# Start the backend server in the background
echo "Starting backend server on http://localhost:8000..."
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start the frontend server in the foreground
echo "Starting frontend server on http://localhost:3000..."
(cd frontend && npm run dev)
FRONTEND_PID=$!

# Wait for all background processes to finish (which they won't, until the script is terminated)
wait $BACKEND_PID $FRONTEND_PID
