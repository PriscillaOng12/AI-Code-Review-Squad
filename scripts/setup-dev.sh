# Development Setup Script
#!/bin/bash

set -e

echo "🚀 Setting up AI Code Review Squad development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual API keys and settings"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
python -m venv venv
source venv/bin/activate || source venv/Scripts/activate  # Windows compatibility
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "✅ Development environment setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit the .env file with your API keys"
echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start the frontend: cd frontend && npm start"
echo "4. Visit http://localhost:3000 to see the application"
echo ""
echo "📚 Useful commands:"
echo "- docker-compose up -d : Start all services"
echo "- docker-compose logs : View service logs"
echo "- docker-compose down : Stop all services"
