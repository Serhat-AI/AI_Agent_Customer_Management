#!/bin/bash
# Unix/Linux/Mac Setup Script for RSD Analysis Agent

set -e

echo "========================================"
echo "RSD Analysis Agent - Setup Script"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

python3 --version

# Get project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Step 1: Create virtual environment
echo ""
echo "Step 1: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
fi

# Step 2: Activate virtual environment
echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing dependencies..."
pip install -r requirements.txt

# Step 4: Setup .env
echo ""
echo "Step 4: Configuring .env..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from template. Please edit with your settings:"
        echo "  vim .env"
    else
        echo "ERROR: .env.example not found"
        exit 1
    fi
fi

# Step 5: Run setup check
echo ""
echo "Step 5: Running setup checks..."
python setup_check.py

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Download credentials.json from Google Cloud Console"
echo "  2. Place credentials.json in: $PROJECT_DIR"
echo "  3. Run: python main.py --init"
echo "  4. Then: python main.py"
echo ""
