#!/bin/bash
# Setup script for Linux/macOS environment
# This script sets up the development/test environment for the secure Flask application

set -e

echo "=== Security Audit Verification Environment Setup ==="
echo "Platform: Linux/macOS"

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating application directories..."
mkdir -p logs config data

# Create example environment file
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from template (update with your secrets)"
else
    echo ".env file already exists"
fi

# Initialize database if needed
echo "Database setup..."
if [ ! -f "appdata.db" ]; then
    echo "Database file will be created on first run"
fi

# Create test config directory
echo "Creating test configuration..."
mkdir -p config
cat > config/test.yaml << 'EOF'
# Test configuration file
app:
  name: secure_app
  version: 1.0.0
  debug: false
database:
  file: appdata.db
  timeout: 5000
EOF

echo ""
echo "=== Setup Complete ==="
echo "To activate the environment, run: source venv/bin/activate"
echo "To run tests, execute: bash run_test.sh"
echo "To run auto tests, execute: python auto_test.py"
