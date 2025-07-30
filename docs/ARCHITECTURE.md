# 🤖 AI Code Review Squad - Technical Architecture

## System Overview

The AI Code Review Squad is a sophisticated multi-agent system designed to provide comprehensive code reviews through specialized AI agents. Each agent focuses on specific aspects of code quality, working together to deliver thorough analysis.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   Frontend      │    │   Admin Panel   │
│   Webhooks      │    │   Dashboard     │    │   Management    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          v                      v                      v
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                             │
│                      (FastAPI + NGINX)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                    Message Queue                               │
│                   (Redis + Celery)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                  Agent Orchestra                               │
│         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│         │  Security   │  │ Performance │  │    Style    │       │
│         │   Agent     │  │   Agent     │  │    Agent    │       │
│         └─────────────┘  └─────────────┘  └─────────────┘       │
│         ┌─────────────┐  ┌─────────────┐                        │
│         │   Logic     │  │Architecture │                        │
│         │   Agent     │  │   Agent     │                        │
│         └─────────────┘  └─────────────┘                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                 │
│         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│         │ PostgreSQL  │  │    Redis    │  │   Vector    │       │
│         │  (Primary)  │  │  (Cache)    │  │ Database    │       │
│         └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                      │
                      v
┌─────────────────────────────────────────────────────────────────┐
│                External Services                               │
│         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│         │  OpenAI     │  │  Anthropic  │  │   GitHub    │       │
│         │    API      │  │    API      │  │     API     │       │

# System Architecture Deep Dive: AI Code Review Squad

## Overview Diagram

![System Architecture](assets/architecture-diagram.png)

## Component Breakdown

### 1. GitHub Integration
- **Webhooks:** Triggers review jobs on PRs
- **OAuth:** Secure repo access
- **PR Comments:** Posts findings directly to GitHub

### 2. FastAPI Backend
- **Async API:** Handles review requests, user auth, and WebSocket connections
- **API Design:** RESTful, type-checked, OpenAPI docs auto-generated
- **Error Handling:** Custom exception handlers, detailed error responses

### 3. Celery + Redis Queue
- **Background Jobs:** Offloads heavy agent analysis
- **Scalability:** Add more workers for higher throughput
- **Retry Logic:** Auto-retries failed jobs

### 4. AgentOrchestra (Multi-Agent Coordinator)
- **Parallel Execution:** Runs 5 agents at once
- **Deduplication:** Merges overlapping findings
- **Prioritization:** Ranks by severity/confidence
- **Conflict Resolution:** If agents disagree, uses risk score + LLM consensus

### 5. Specialized Agents
- **SecurityAgent:** Pattern matching, AST, LLM for OWASP/CWE
- **PerformanceAgent:** Big O, memory, anti-patterns
- **StyleAgent:** PEP8, ESLint, naming, docs
- **LogicAgent:** Edge cases, unreachable code, bug patterns
- **ArchitectureAgent:** SOLID, design patterns, code structure

### 6. PostgreSQL Database
- **Schema:** Users, reviews, findings, agent runs, audit logs
- **Indexes:** On repo, PR, severity for fast queries
- **Migrations:** Alembic for versioned schema changes

### 7. React Frontend
- **Material-UI:** Clean, accessible dashboard
- **WebSocket Client:** Real-time updates as agents finish
- **Filtering:** By severity, agent, file, etc.

## Data Flow

1. PR opened/updated on GitHub
2. Webhook hits FastAPI → queues review job
3. Celery worker runs AgentOrchestra
4. Agents analyze code in parallel
5. Findings deduped, prioritized, stored in DB
6. WebSocket pushes updates to frontend
7. User sees live results, can filter and drill down

## Key Technical Decisions

- **Async everywhere:** FastAPI, DB, Celery for speed
- **Multi-agent pattern:** Specialization = better accuracy
- **WebSocket:** Real-time UX, not just polling
- **Containerization:** Docker for local/prod parity
- **Type safety:** TypeScript + Python type hints

## Security Implementation
- **JWT Auth:** Secure API endpoints
- **Secret Management:** .env + Docker secrets
- **Input Validation:** Pydantic models, frontend checks
- **Audit Logging:** All review actions logged

## Error Handling & Observability
- **Centralized error logging:** Sentry + custom logs
- **Health checks:** /health endpoint, Prometheus metrics
- **Alerting:** Email/slack on job failures

## Scalability Considerations
- **Horizontal scaling:** Add more Celery workers, DB replicas
- **Caching:** Redis for hot queries
- **Stateless API:** Easy to scale out

## Technology Justifications
- **FastAPI:** Async, type-safe, great OpenAPI support
- **Celery/Redis:** Proven for distributed job queues
- **PostgreSQL:** Reliable, strong relational model
- **React/TypeScript:** Modern, maintainable frontend
- **Docker:** Consistent local/prod environments

---

_Building this system made me appreciate how much architecture is about trade-offs. I learned a ton about distributed systems, error handling, and why real-time UX is so hard (but worth it!)._
│         └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway (FastAPI)
- **Purpose**: Central entry point for all requests
- **Features**: 
  - Rate limiting
  - Authentication/Authorization
  - Request validation
  - WebSocket support for real-time updates
- **Endpoints**:
  - `/api/v1/reviews` - Review management
  - `/api/v1/repositories` - Repository configuration
  - `/api/v1/agents` - Agent status and configuration
  - `/webhook/github` - GitHub webhook handler

### 2. Agent Orchestra
The heart of the system where specialized AI agents collaborate:

#### SecurityAgent
- **Focus**: Security vulnerabilities and threats
- **Capabilities**:
  - SQL injection detection
  - XSS vulnerability identification
  - Authentication/authorization flaws
  - Cryptographic issues
  - OWASP Top 10 compliance
- **Model**: GPT-4 (high precision required)
- **Priority**: Critical (Level 1)

#### PerformanceAgent
- **Focus**: Performance optimization opportunities
- **Capabilities**:
  - Algorithm complexity analysis (Big O)
  - Memory leak detection
  - Database query optimization
  - Caching opportunities
  - Resource usage patterns
- **Model**: GPT-4
- **Priority**: High (Level 2)

#### StyleAgent
- **Focus**: Code style and formatting standards
- **Capabilities**:
  - Language-specific style guide enforcement (PEP8, ESLint, etc.)
  - Naming convention validation
  - Code formatting standards
  - Documentation completeness
  - Comment quality assessment
- **Model**: GPT-3.5-turbo (cost-effective for style checks)
- **Priority**: Medium (Level 3)

#### LogicAgent
- **Focus**: Logical correctness and edge cases
- **Capabilities**:
  - Edge case identification
  - Null pointer analysis
  - Control flow validation
  - Input validation checks
  - Business logic verification
- **Model**: GPT-4
- **Priority**: Critical (Level 1)

#### ArchitectureAgent
- **Focus**: System design and code organization
- **Capabilities**:
  - Design pattern recognition
  - SOLID principles validation
  - Dependency analysis
  - Code organization assessment
  - Maintainability scoring
- **Model**: GPT-4
- **Priority**: High (Level 2)

### 3. Message Queue System (Celery + Redis)
- **Purpose**: Asynchronous task processing
- **Features**:
  - Parallel agent execution
  - Task prioritization
  - Retry mechanisms
  - Progress tracking
- **Queues**:
  - `reviews` - Code review tasks
  - `notifications` - User notifications
  - `maintenance` - System maintenance tasks

### 4. Data Layer

#### PostgreSQL (Primary Database)
- **Purpose**: Persistent data storage
- **Tables**:
  - `users` - User management
  - `repositories` - Repository configuration
  - `code_reviews` - Review sessions
  - `agent_responses` - Agent analysis results
  - `file_analyses` - File-level analysis
  - `review_metrics` - Performance metrics

#### Redis (Cache & Queue)
- **Purpose**: Caching and message brokering
- **Use Cases**:
  - Session storage
  - API response caching
  - File analysis caching
  - Real-time updates
  - Rate limiting

### 5. Frontend Dashboard (React.js)
- **Purpose**: User interface for review management
- **Features**:
  - Real-time review progress
  - Agent findings visualization
  - Repository management
  - Performance analytics
  - Configuration management

## Data Flow

### 1. Review Trigger
```
GitHub Webhook → API Gateway → Webhook Service → Queue Task
```

### 2. Agent Processing
```
Queue → Agent Orchestra → Multiple Agents (Parallel) → Result Aggregation
```

### 3. Result Storage
```
Agent Results → Database → Cache → WebSocket Broadcast → Frontend Update
```

## Scalability Features

### Horizontal Scaling
- **Agent Workers**: Can be scaled independently
- **API Servers**: Stateless design allows multiple instances
- **Database**: Read replicas for improved performance

### Caching Strategy
- **Level 1**: In-memory agent result caching
- **Level 2**: Redis caching for API responses
- **Level 3**: File analysis result caching

### Performance Optimizations
- **Parallel Processing**: Agents run concurrently
- **Smart Filtering**: Only analyze relevant files per agent
- **Result Memoization**: Cache similar analysis results
- **Connection Pooling**: Efficient database connections

## Security Measures

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- GitHub OAuth integration

### Data Protection
- API key encryption
- Webhook signature verification
- HTTPS everywhere
- Rate limiting

### Code Privacy
- Temporary file storage
- Automatic cleanup
- No persistent code storage
- Audit logging

## Monitoring & Observability

### Metrics Collection
- **Business Metrics**: Review completion rates, finding accuracy
- **Technical Metrics**: Response times, error rates, resource usage
- **Agent Metrics**: Execution times, token usage, cost tracking

### Logging
- Structured logging with correlation IDs
- Agent execution traces
- Error tracking with Sentry
- Performance monitoring

### Health Checks
- Service health endpoints
- Database connectivity checks
- External API availability
- Agent responsiveness

## Deployment Architecture

### Development Environment
```
Local Machine → Docker Compose → Hot Reload
```

### Staging Environment
```
GitHub Actions → Docker Build → Staging Cluster → Integration Tests
```

### Production Environment
```
GitHub Actions → Security Scan → Docker Registry → Kubernetes → Rolling Update
```

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.11 | REST API and WebSocket server |
| **Frontend** | React.js + TypeScript | User interface |
| **Database** | PostgreSQL 15 | Primary data storage |
| **Cache** | Redis 7 | Caching and message broker |
| **Queue** | Celery | Asynchronous task processing |
| **AI Models** | OpenAI GPT-4, GPT-3.5-turbo | Code analysis |
| **Containerization** | Docker + Docker Compose | Development and deployment |
| **Orchestration** | Kubernetes | Production deployment |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **CI/CD** | GitHub Actions | Automated testing and deployment |

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Review Completion Time | < 2 minutes | TBD |
| API Response Time | < 200ms (95th percentile) | TBD |
| Concurrent Reviews | 100+ | TBD |
| System Uptime | 99.9% | TBD |
| False Positive Rate | < 10% | TBD |

## Future Enhancements

### Phase 2 Features
- Machine learning for false positive reduction
- Custom rule creation interface
- Multi-language support expansion
- IDE plugin integration

### Phase 3 Features
- Advanced analytics and reporting
- Team collaboration features
- Integration with more CI/CD platforms
- Custom agent development SDK
