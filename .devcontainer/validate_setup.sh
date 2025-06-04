#!/bin/bash

echo "=== Dev Container Setup Validation ==="
echo

# Check Python version
echo "1. Python Version:"
python --version
echo

# Check if all required packages are installed
echo "2. Required packages:"
python -c "
import uvicorn
import fastapi
import debugpy
print('✓ uvicorn, fastapi, debugpy available')
"
echo

# Check environment variables
echo "3. Environment Variables:"
echo "PYTHONPATH: $PYTHONPATH"
echo "PYTHONDONTWRITEBYTECODE: $PYTHONDONTWRITEBYTECODE"
echo "PYTHONUNBUFFERED: $PYTHONUNBUFFERED"
echo

# Check workspace mounting
echo "4. Workspace Structure:"
ls -la /app | head -10
echo

# Test basic imports
echo "5. Application imports:"
python -c "
try:
    import main
    print('✓ main.py can be imported')
except Exception as e:
    print(f'✗ Error importing main.py: {e}')

try:
    from app.engine_dag import DAG
    print('✓ DAG can be imported')
except Exception as e:
    print(f'✗ Error importing DAG: {e}')
"
echo

echo "=== Validation Complete ==="
echo
echo "To start the API server, run:"
echo "uvicorn main:app --reload --host 0.0.0.0 --port 8081"
echo
echo "To start debugging, run:"
echo "python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --reload --host 0.0.0.0 --port 8081"