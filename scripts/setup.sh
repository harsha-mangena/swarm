#!/bin/bash

# SwarmOS setup script

echo "Setting up SwarmOS..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check for Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
poetry install

# Check for Node.js (for Vue frontend)
if command -v npm &> /dev/null; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo "Frontend dependencies installed."
else
    echo "Warning: Node.js not found. Frontend will not work."
    echo "Please install Node.js and run 'cd frontend && npm install'"
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env with your API keys"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Start infrastructure: ./scripts/run.sh start"
echo "3. Start backend: uvicorn backend.main:app --reload"

