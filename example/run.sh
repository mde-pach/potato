#!/usr/bin/env bash

# Script to run the example FastAPI application

cd "$(dirname "$0")"

# Set PYTHONPATH to include the parent potato package
export PYTHONPATH="../src:."

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "Installing uvicorn..."
    uv pip install 'uvicorn[standard]>=0.32.0'
fi

# Run the application
echo "Starting Potato Example - Blog Management System..."
echo "Server will be available at: http://127.0.0.1:8000"
echo "API docs at: http://127.0.0.1:8000/docs"
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
