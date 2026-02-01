#!/bin/bash
# Setup script for Open Ag Library

set -e

echo "Setting up Open Ag Library..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your database credentials"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your database credentials"
echo "2. Create PostgreSQL database: createdb open_ag_library"
echo "3. Initialize schema: psql -d open_ag_library -f schema.sql"
echo "4. Activate venv: source venv/bin/activate"
echo "5. Analyze schemas: python analyze_schema.py"
echo "6. Import data: python import_faostat.py"
