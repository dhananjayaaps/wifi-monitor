#!/bin/bash
# Development setup script
echo "Setting up development environment..."
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../pi-agent && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
echo "Development environment ready!"
