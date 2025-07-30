#!/bin/bash

# AI Code Review Squad Deployment Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Setting up AI Code Review Squad..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed ✓"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Frontend development will require Node.js."
    else
        NODE_VERSION=$(node --version)
        print_status "Node.js $NODE_VERSION is installed ✓"
    fi
}

# Create environment files
create_env_files() {
    print_status "Creating environment files..."
    
    # Backend environment
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        print_status "Created backend/.env from template"
        print_warning "Please update backend/.env with your actual API keys and settings"
    else
        print_status "Backend .env file already exists"
    fi
    
    # Frontend environment  
    if [ ! -f "frontend/.env" ]; then
        cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_GITHUB_CLIENT_ID=your_github_client_id
EOF
        print_status "Created frontend/.env file"
        print_warning "Please update frontend/.env with your GitHub OAuth app client ID"
    else
        print_status "Frontend .env file already exists"
    fi
}

# Install backend dependencies
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Created Python virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    print_status "Installed Python dependencies"
    
    cd ..
}

# Install frontend dependencies
setup_frontend() {
    print_status "Setting up frontend..."
    
    if command -v npm &> /dev/null; then
        cd frontend
        npm install
        print_status "Installed Node.js dependencies"
        cd ..
    else
        print_warning "npm not found. Skipping frontend dependency installation."
    fi
}

# Start services with Docker
start_services() {
    print_status "Starting services with Docker..."
    
    # Start PostgreSQL and Redis
    docker-compose up -d postgres redis
    
    print_status "Database and Redis services started"
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    until docker-compose exec postgres pg_isready -U codereviewer -d ai_code_review; do
        sleep 2
    done
    
    print_status "PostgreSQL is ready ✓"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    cd backend
    source venv/bin/activate
    
    # Create migration if it doesn't exist
    if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions 2>/dev/null)" ]; then
        alembic revision --autogenerate -m "Initial migration"
        print_status "Created initial migration"
    fi
    
    # Run migrations
    alembic upgrade head
    print_status "Database migrations completed ✓"
    
    cd ..
}

# Test the setup
test_setup() {
    print_status "Testing setup..."
    
    cd backend
    source venv/bin/activate
    
    # Run a quick test
    python -c "
import asyncio
from app.agents.security_agent import SecurityAgent
from app.agents.base import CodeFile

async def test():
    agent = SecurityAgent()
    file = CodeFile('test.py', 'print(\"hello world\")', 'python')
    print('SecurityAgent test passed ✓')

asyncio.run(test())
"
    
    print_status "Agent test completed ✓"
    cd ..
}

# Create sample configuration
create_sample_config() {
    print_status "Creating sample configuration..."
    
    cat > config.yaml << EOF
# AI Code Review Squad Configuration
agents:
  security:
    enabled: true
    priority: 1
    timeout_seconds: 300
    max_files_per_agent: 50
  
  performance:
    enabled: true
    priority: 2
    timeout_seconds: 300
    max_files_per_agent: 50
  
  style:
    enabled: true
    priority: 3
    timeout_seconds: 180
    max_files_per_agent: 100
  
  logic:
    enabled: true
    priority: 2
    timeout_seconds: 300
    max_files_per_agent: 50
  
  architecture:
    enabled: true
    priority: 3
    timeout_seconds: 300
    max_files_per_agent: 30

# LLM Configuration
llm:
  openai:
    model: "gpt-4"
    max_tokens: 2000
    temperature: 0.1
  
  anthropic:
    model: "claude-3-sonnet-20240229"
    max_tokens: 2000

# GitHub Integration
github:
  webhook_secret: "your_webhook_secret"
  oauth:
    client_id: "your_client_id"
    client_secret: "your_client_secret"
EOF
    
    print_status "Created config.yaml template"
}

# Display final instructions
show_final_instructions() {
    print_status "Setup completed! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Update backend/.env with your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GITHUB_CLIENT_SECRET"
    echo ""
    echo "2. Update frontend/.env with your GitHub OAuth client ID"
    echo ""
    echo "3. Start the development servers:"
    echo "   Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "   Frontend: cd frontend && npm start"
    echo "   Celery:   cd backend && source venv/bin/activate && celery -A app.celery worker --loglevel=info"
    echo ""
    echo "4. Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "5. Database tools:"
    echo "   PostgreSQL: postgresql://codereviewer:securepassword@localhost:5432/ai_code_review"
    echo "   Redis:      redis://localhost:6379"
    echo ""
    print_status "Happy coding! 🚀"
}

# Main execution
main() {
    print_status "Starting AI Code Review Squad setup..."
    
    check_docker
    check_node
    create_env_files
    setup_backend
    setup_frontend
    start_services
    run_migrations
    test_setup
    create_sample_config
    show_final_instructions
}

# Run main function
main
