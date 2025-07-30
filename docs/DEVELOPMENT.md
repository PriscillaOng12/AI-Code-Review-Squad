# 🚀 AI Code Review Squad - Development Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Initial Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ai-code-review-squad
```

2. **Run the setup script**
```bash
./scripts/setup-dev.sh
```

3. **Configure environment variables**
```bash
# Copy and edit the environment file
cp .env.example .env
# Edit .env with your API keys and settings
```

4. **Start the development environment**
```bash
# Start databases
docker-compose up -d postgres redis

# Start backend (in new terminal)
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# Start frontend (in new terminal)
cd frontend
npm start
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
ai-code-review-squad/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agent implementations
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Test suite
│   ├── Dockerfile          # Backend container
│   └── requirements.txt    # Python dependencies
├── frontend/               # React.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   ├── Dockerfile          # Frontend container
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
├── scripts/                # Setup and utility scripts
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Development environment
└── README.md              # Project overview
```

## Development Workflow

### 1. Creating New Features

#### Backend Development
```bash
# Create a new feature branch
git checkout -b feature/new-agent

# Navigate to backend
cd backend
source venv/bin/activate

# Create new agent
mkdir app/agents/new_agent
touch app/agents/new_agent/__init__.py
touch app/agents/new_agent/agent.py

# Add tests
touch tests/test_new_agent.py

# Run tests
pytest tests/

# Check code quality
black app/
isort app/
flake8 app/
mypy app/
```

#### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Create new component
mkdir src/components/NewComponent
touch src/components/NewComponent/NewComponent.tsx
touch src/components/NewComponent/index.ts

# Add styles
touch src/components/NewComponent/NewComponent.module.css

# Run tests
npm test

# Check code quality
npm run lint
npm run lint:fix
```

### 2. Agent Development

#### Creating a New Agent

1. **Create agent class**
```python
# app/agents/my_agent/agent.py
from typing import List, Tuple
from app.agents.base import BaseAgent, Finding, CodeFile

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent")
    
    async def _perform_analysis(self, files: List[CodeFile], context: dict) -> Tuple[List[Finding], int]:
        # Implement analysis logic
        findings = []
        tokens_used = 0
        
        for file in files:
            # Analyze file
            prompt = self._create_prompt([file], context)
            response, tokens = await self._call_llm(prompt)
            tokens_used += tokens
            
            # Parse response to findings
            file_findings = self._parse_llm_response(response)
            findings.extend(file_findings)
        
        return findings, tokens_used
    
    def _create_prompt(self, files: List[CodeFile], context: dict) -> str:
        # Create specialized prompt for this agent
        return f"Analyze this code for my specific criteria: {files[0].content}"
```

2. **Register agent in orchestra**
```python
# app/services/agent_orchestra.py
from app.agents.my_agent.agent import MyAgent

class AgentOrchestra:
    def __init__(self):
        self.agents = [
            SecurityAgent(),
            PerformanceAgent(),
            StyleAgent(),
            LogicAgent(),
            ArchitectureAgent(),
            MyAgent(),  # Add new agent
        ]
```

3. **Add configuration**
```python
# app/core/config.py
AGENT_CONFIGS = {
    # ... existing agents
    "my_agent": {
        "enabled": True,
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "timeout": 120,
        "priority": 2,
        "description": "My custom agent description"
    }
}
```

4. **Write tests**
```python
# tests/agents/test_my_agent.py
import pytest
from app.agents.my_agent.agent import MyAgent
from app.agents.base import CodeFile

@pytest.mark.asyncio
async def test_my_agent_analysis():
    agent = MyAgent()
    
    files = [
        CodeFile(
            path="test.py",
            content="def test(): pass",
            language="python",
            size=100,
            hash="abc123"
        )
    ]
    
    result = await agent.analyze_code(files)
    
    assert result.agent_type == "my_agent"
    assert isinstance(result.findings, list)
```

### 3. API Development

#### Adding New Endpoints
```python
# app/api/v1/endpoints/my_endpoint.py
from fastapi import APIRouter, Depends
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    # Implementation
    return {"items": []}

@router.post("/")
async def create_item(item_data: dict, db: AsyncSession = Depends(get_db)):
    # Implementation
    return {"created": True}
```

#### Register in main router
```python
# app/api/v1/api.py
from app.api.v1.endpoints import my_endpoint

api_router.include_router(my_endpoint.router, prefix="/my-endpoint", tags=["my-endpoint"])
```

### 4. Frontend Development

#### Creating Components
```typescript
// src/components/ReviewCard/ReviewCard.tsx
import React from 'react';
import { Card, CardContent, Typography, Chip } from '@mui/material';

interface ReviewCardProps {
  review: Review;
  onClick?: () => void;
}

export const ReviewCard: React.FC<ReviewCardProps> = ({ review, onClick }) => {
  return (
    <Card onClick={onClick} className="review-card">
      <CardContent>
        <Typography variant="h6">{review.commit_hash}</Typography>
        <Chip 
          label={review.status} 
          color={getStatusColor(review.status)}
        />
      </CardContent>
    </Card>
  );
};

function getStatusColor(status: string) {
  switch (status) {
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'in_progress': return 'warning';
    default: return 'default';
  }
}
```

#### API Service Functions
```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const reviewService = {
  async getReviews(params?: any) {
    const response = await api.get('/reviews', { params });
    return response.data;
  },
  
  async getReview(id: string) {
    const response = await api.get(`/reviews/${id}`);
    return response.data;
  },
  
  async createReview(data: any) {
    const response = await api.post('/reviews', data);
    return response.data;
  },
};
```

## Testing

### Backend Testing
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_security_agent.py

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/
```

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test ReviewCard.test.tsx

# Run e2e tests
npm run test:e2e
```

## Database Operations

### Running Migrations
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Database Reset
```bash
# Stop containers
docker-compose down

# Remove volumes
docker-compose down -v

# Restart
docker-compose up -d postgres redis
```

## Debugging

### Backend Debugging
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use ipdb for better debugging
import ipdb; ipdb.set_trace()

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Debugging
```typescript
// Use React Developer Tools
console.log('Debug info:', data);

// Add breakpoints in browser DevTools
debugger;

// Enable verbose logging
localStorage.setItem('debug', 'true');
```

## Performance Optimization

### Backend Performance
- Use async/await for I/O operations
- Implement database connection pooling
- Add Redis caching for expensive operations
- Use background tasks for heavy processing

### Frontend Performance
- Implement code splitting with React.lazy()
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Optimize bundle size with webpack-bundle-analyzer

## Code Quality

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Style
- **Backend**: Black, isort, flake8, mypy
- **Frontend**: ESLint, Prettier, TypeScript

### Documentation
- Write docstrings for all functions
- Update README when adding features
- Document API changes in OpenAPI spec
- Keep architecture docs up to date

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   ```

2. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # View logs
   docker-compose logs postgres
   ```

3. **Agent timeout issues**
   ```python
   # Increase timeout in config
   AGENT_CONFIGS["my_agent"]["timeout"] = 300
   ```

4. **Memory issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Increase Docker memory limit
   # Docker Desktop -> Settings -> Resources
   ```

### Getting Help

1. **Check logs**
   ```bash
   # Backend logs
   docker-compose logs backend
   
   # Frontend logs
   npm start  # Check console output
   ```

2. **Enable debug mode**
   ```bash
   # Set in .env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

3. **Common commands**
   ```bash
   # Reset everything
   docker-compose down -v && docker-compose up -d
   
   # Rebuild containers
   docker-compose build --no-cache
   
   # Clean Python cache
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -delete
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

### Pull Request Guidelines
- Write clear commit messages
- Include tests for new features
- Update documentation
- Follow code style guidelines
- Keep PRs focused and small
