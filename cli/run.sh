#!/bin/bash
# BOTUVIC CLI Runner Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: venv directory not found. Please create it first:"
    echo "  python3 -m venv venv"
    exit 1
fi

# Install/update package if needed
echo "Installing/updating BOTUVIC..."
python3 -m pip install -e . --quiet

# Run botuvic
echo "Starting BOTUVIC..."
botuvic

