#!/bin/bash

# Find and remove all .pyc files to prevent caching issues
find . -type f -name "*.pyc" -delete

echo "Starting backend server..."
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
