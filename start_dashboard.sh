#!/bin/bash
# Quick launcher for the dashboard

cd "$(dirname "$0")"

echo "============================================================"
echo "  GPU/RAM Price Index Dashboard"
echo "============================================================"
echo ""
echo "Starting server..."
echo "Dashboard will be available at: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

python3 dashboard.py
