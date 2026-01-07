#!/bin/bash
echo "Starting Chat Server..."
echo "Make sure you have installed dependencies: pip install -r requirements.txt"
echo ""
python3 -m uvicorn main:app --host 0.0.0.0 --port 10000 --reload

