#!/bin/bash
set -e

# Initialize database
echo "Initializing database..."
python init_database.py

# Start backend in background
echo "Starting backend..."
python start_server.py --port 8000 &

# Wait for backend to be ready (optional, but good practice)
sleep 5

# Start frontend
echo "Starting frontend..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
