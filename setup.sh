#!/bin/bash

# Logistics PLC Python Setup Script
# This script sets up the development environment and installs dependencies

echo "🚀 Setting up Logistics PLC Python Application"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p app/database/migrations

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "✅ Environment file created (.env). Please review and modify as needed."
else
    echo "⚙️  Environment file already exists"
fi

# Initialize database (create tables)
echo "🗃️  Initializing database..."
python3 -c "
import sys
sys.path.append('.')
from config.database_config import init_database, test_connection
if test_connection():
    init_database()
    print('✅ Database initialized successfully')
else:
    print('⚠️  Database connection failed - check your settings')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To run the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start the application: python main.py"
echo ""
echo "Web Dashboard will be available at: http://localhost:5000"
echo ""
echo "📝 Next steps:"
echo "  - Review and update .env file with your PLC settings"
echo "  - Configure your PLC communication parameters"
echo "  - Test the connection with your PLC"
echo ""
