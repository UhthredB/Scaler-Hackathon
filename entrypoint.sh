#!/bin/bash
set -e

echo "Starting Job Application Simulator..."
echo "PORT: ${PORT:-7860}"
echo "Working directory: $(pwd)"

# Test imports
python3 -c "
import sys
sys.path.insert(0, '.')
print('Testing imports...')
from mock_data import get_jobs
print('✓ mock_data OK')
from models import JobPosting
print('✓ models OK')
from server.main import app
print('✓ server.main OK')
print('All imports successful!')
"

# Start the server
echo "Starting uvicorn on port ${PORT:-7860}..."
exec uvicorn server.main:app --host 0.0.0.0 --port "${PORT:-7860}"
