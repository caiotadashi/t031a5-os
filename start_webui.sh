#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv/"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Run the web application
echo "Starting web application..."
python -m webui.app

# Keep the script running in case of errors
if [ $? -ne 0 ]; then
    echo "The web application encountered an error. Press any key to exit..."
    read -n 1 -s
fi
