#!/bin/bash

# REWE Receipt Analyzer Launch Script
# This script loads environment variables from .env and runs the analyzer

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env  # or use your preferred editor"
    exit 1
fi

# Load environment variables from .env
echo "Loading credentials from .env..."
set -a
source .env
set +a

# Check if Proton Bridge is running (if using ProtonMail)
if [ "$IMAP_SERVER" = "127.0.0.1" ] && [ "$IMAP_PORT" = "1143" ]; then
    if ! nc -z 127.0.0.1 1143 2>/dev/null; then
        echo "Warning: Proton Bridge doesn't appear to be running!"
        echo "Please start Proton Bridge before running this script."
        echo "Run: protonmail-bridge"
        exit 1
    fi
    echo "Proton Bridge detected and running."
fi

# Run the analyzer
echo "Starting REWE Receipt Analyzer..."
python main.py
