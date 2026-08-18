#!/bin/bash

echo ""
echo "  ========================================"
echo "   Mini AI Security Lab - Setup"
echo "  ========================================"
echo ""

# Check Python
echo "  Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "  X Python3 not found!"
    echo "    Please install Python 3.10+"
    exit 1
fi
echo "  + $(python3 --version) found"
echo ""

# Create virtual environment
echo "  Creating environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  + Environment created"
else
    echo "  + Environment already exists"
fi
echo ""

# Activate and install
echo "  Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "  + Dependencies ready"
echo ""

# Start application
echo "  ========================================"
echo "   Starting AI Security Lab..."
echo "  ========================================"
echo ""
echo "  Open: http://127.0.0.1:5000"
echo "  Press Ctrl+C to stop"
echo ""

python app/main.py
