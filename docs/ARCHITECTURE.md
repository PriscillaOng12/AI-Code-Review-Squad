# System Architecture

## Table of Contents
- [Overview](#overview)
- [System Design](#system-design)
- [Data Architecture](#data-architecture)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)
- [Technology Decisions](#technology-decisions)
- [Deployment Architecture](#deployment-architecture)

## Overview

AI Code Review Squad is designed as a **distributed, event-driven microservices architecture** optimized for high-throughput code analysis with sub-minute latency requirements. The system processes GitHub webhook events through a multi-agent pipeline that scales horizontally based on workload.

## System Design

### High-Level Architecture

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'clusterBkg': 'transparent', 'clusterBorder': '#ffffff', 'edgeLabelBackground': 'transparent'}}}%%
graph TB
    subgraph "External Systems"
        GITHUB[GitHub Repository<br/>Pull Requests]
        SLACK[Slack Notifications]
        DATADOG[DataDog APM]
    end
    
    subgraph "Load Balancer & Gateway"
        LB[Application Load Balancer<br/>AWS ALB or Nginx]
        WAF[Web Application Firewall<br/>Rate Limiting and DDoS Protection]
    end
    
    subgraph "API Layer"
        API1[FastAPI Instance 1<br/>8 CPU and 16GB RAM]
        API2[FastAPI Instance 2<br/>8 CPU and 16GB RAM]
        API3[FastAPI Instance N<br/>Auto-scaling Group]
    end
    
    subgraph "Authentication & Authorization"
        JWT[JWT Token Validation]
        RBAC[Role-Based Access Control<br/>Four Permission Levels<br/>Viewer to Owner]
        RATELIMIT[Token Bucket Rate Limiter<br/>100 requests per minute per tenant]
    end
    
    subgraph "Message Queue Layer"
        REDIS_BROKER[Redis Cluster<br/>Celery Broker<br/>3 nodes with sentinels]
        REDIS_CACHE[Redis Cache<br/>Session and API Cache<br/>separate instance]
    end
    
    subgraph "Worker Pool"
        W1[Security Agent Worker<br/>2 CPU and 4GB RAM]
        W2[Style Agent Worker<br/>1 CPU and 2GB RAM] 
        W3[Logic Agent Worker<br/>2 CPU and 4GB RAM]
        W4[Performance Agent Worker<br/>2 CPU and 4GB RAM]
        W5[Architecture Agent Worker<br/>1 CPU and 2GB RAM]
        W6[Multi-Agent Worker Pool<br/>KEDA Auto-scaling 1 to 10]
    end
    
    subgraph "Data Layer"
        PGPRIMARY[PostgreSQL Primary<br/>16 CPU and 64GB RAM<br/>2TB SSD Storage]
        PGREPLICA[PostgreSQL Read Replica<br/>8 CPU and 32GB RAM<br/>Analytics Queries]
        S3[S3 Bucket<br/>Analytics Exports<br/>Parquet Files]
    end
    
    subgraph "Analytics Pipeline"
        SPARK[PySpark Cluster<br/>EMR or Databricks]
        JUPYTER[Jupyter Notebooks<br/>KPI Analysis]
        AIRFLOW[Apache Airflow<br/>ETL Orchestration]
    end
    
    subgraph "Monitoring Stack"
        PROMETHEUS[Prometheus<br/>Metrics Collection]
        GRAFANA[Grafana<br/>Dashboards and Alerts]
        JAEGER[Jaeger<br/>Distributed Tracing]
        ELK[ELK Stack<br/>Log Aggregation]
    end
    
    GITHUB -->|Webhook| WAF
    WAF --> LB
    LB --> API1
    LB --> API2  
    LB --> API3
    
    API1 --> JWT
    API2 --> RBAC
    API3 --> RATELIMIT
    
    API1 --> REDIS_BROKER
    API2 --> REDIS_CACHE
    API3 --> PGPRIMARY
    
    REDIS_BROKER --> W1
    REDIS_BROKER --> W2
    REDIS_BROKER --> W3
    REDIS_BROKER --> W4
    REDIS_BROKER --> W5
    REDIS_BROKER --> W6
    
    W1 --> PGPRIMARY
    W2 --> PGPRIMARY
    W3 --> PGPRIMARY
    W4 --> PGPRIMARY
    W5 --> PGPRIMARY
    W6 --> PGPRIMARY
    
    PGPRIMARY -.->|Streaming Replication| PGREPLICA
    PGREPLICA --> S3
    S3 --> SPARK
    SPARK --> JUPYTER
    
    API1 --> PROMETHEUS
    W1 --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    
    style GITHUB fill:#ff6b6b,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style SLACK fill:#4ecdc4,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DATADOG fill:#45b7d1,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style LB fill:#a8e6cf,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style WAF fill:#ff8b94,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style API1 fill:#87ceeb,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style API2 fill:#87ceeb,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style API3 fill:#87ceeb,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style JWT fill:#ffd93d,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style RBAC fill:#ffd93d,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style RATELIMIT fill:#ffd93d,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style REDIS_BROKER fill:#ff9ff3,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style REDIS_CACHE fill:#ff9ff3,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style W1 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style W2 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style W3 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style W4 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style W5 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style W6 fill:#c7ecee,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style PGPRIMARY fill:#a8e6cf,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style PGREPLICA fill:#c8e6c9,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style S3 fill:#ffcdd2,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style SPARK fill:#fff9c4,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style JUPYTER fill:#ffcc80,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style AIRFLOW fill:#f8bbd9,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    
    style PROMETHEUS fill:#e1bee7,stroke:#ffffff,stroke-width:3px,color:#2c3e50
    style GRAFANA fill:#b39ddb,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style JAEGER fill:#9fa8da,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style ELK fill:#90caf9,stroke:#ffffff,stroke-width:3px,color:#2c3e50
```

### Request Flow Architecture

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'actorBkg': 'transparent', 'actorTextColor': '#ffffff', 'actorLineColor': '#ffffff', 'activationBkgColor': 'transparent', 'activationBorderColor': '#ffffff', 'loopTextColor': '#ffffff', 'noteBkgColor': 'transparent', 'noteTextColor': '#ffffff', 'noteBorderColor': '#ffffff', 'messageLine0': '#ffffff', 'messageLine1': '#ffffff', 'messageText': '#ffffff', 'labelTextColor': '#ffffff'}}}%%
sequenceDiagram
    participant GH as GitHub
    participant API as FastAPI API
    participant AUTH as Auth Layer
    participant QUEUE as Redis Queue
    participant SEC as Security Agent
    participant STY as Style Agent
    participant LOG as Logic Agent
    participant PERF as Performance Agent
    participant ARCH as Architecture Agent
    participant DB as PostgreSQL
    participant CACHE as Redis Cache
    
    GH->>API: POST /webhooks/github<br/>(PR opened/updated)
    API->>AUTH: Verify webhook signature
    AUTH-->>API: Signature valid
    
    API->>DB: Create Review record
    DB-->>API: Review ID
    
    API->>QUEUE: Enqueue 5 agent tasks
    Note over QUEUE: Parallel task distribution
    
    par Security Analysis
        QUEUE->>SEC: run_security_agent(review_id)
        SEC->>API: Fetch PR diff
        SEC->>SEC: Analyze for vulnerabilities
        SEC->>DB: Store findings
    and Style Analysis  
        QUEUE->>STY: run_style_agent(review_id)
        STY->>API: Fetch PR diff
        STY->>STY: Check formatting rules
        STY->>DB: Store findings
    and Logic Analysis
        QUEUE->>LOG: run_logic_agent(review_id)
        LOG->>API: Fetch PR diff  
        LOG->>LOG: Detect code smells
        LOG->>DB: Store findings
    and Performance Analysis
        QUEUE->>PERF: run_performance_agent(review_id)
        PERF->>API: Fetch PR diff
        PERF->>PERF: Find bottlenecks
        PERF->>DB: Store findings
    and Architecture Analysis
        QUEUE->>ARCH: run_architecture_agent(review_id)
        ARCH->>API: Fetch PR diff
        ARCH->>ARCH: Check design patterns
        ARCH->>DB: Store findings
    end
    
    Note over DB: All agents complete
    DB->>API: Update review status: completed
    API->>CACHE: Cache results (TTL: 1h)
    API->>GH: Post review comments
```

## Data Architecture

### Database Schema Design

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'entityBkg': 'transparent', 'entityTextColor': '#ffffff', 'relationshipLabelColor': '#ffffff', 'relationshipLabelBackground': 'transparent', 'entityBorderColor': '#ffffff'}}}%%
erDiagram
    TENANTS ||--o{ USERS : "belongs_to"
    TENANTS ||--o{ PROJECTS : "owns"
    PROJECTS ||--o{ REPOS : "contains"
    REPOS ||--o{ REVIEWS : "has"
    REVIEWS ||--o{ AGENT_RUNS : "spawns"
    AGENT_RUNS ||--o{ FINDINGS : "produces"
    TENANTS ||--o{ AUDIT_LOG : "tracks"
    USERS ||--o{ AUDIT_LOG : "performs"
    TENANTS ||--o{ API_KEYS : "manages"
    
    TENANTS {
        uuid id PK
        string name
        string slug UK
        timestamp created_at
    }
    
    USERS {
        uuid id PK
        uuid tenant_id FK
        string email UK
        string role
        string github_id
        timestamp created_at
    }
    
    PROJECTS {
        uuid id PK
        uuid tenant_id FK
        string name
        timestamp created_at
    }
    
    REPOS {
        uuid id PK
        uuid project_id FK
        string provider
        string external_id
        string name
        string default_branch
        timestamp created_at
    }
    
    REVIEWS {
        uuid id PK
        uuid repo_id FK
        string pr_number
        enum status
        json stats_json
        timestamp created_at
        timestamp updated_at
    }
    
    AGENT_RUNS {
        uuid id PK
        uuid review_id FK
        string agent_name
        enum status
        integer duration_ms
        json metrics_json
        timestamp started_at
        timestamp finished_at
    }
    
    FINDINGS {
        uuid id PK
        uuid review_id FK
        uuid agent_run_id FK
        string file_path
        integer start_line
        integer end_line
        enum severity
        string title
        text description
        text suggested_fix
        float confidence
        string rule_id
        timestamp created_at
    }
    
    AUDIT_LOG {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string action
        string entity
        uuid entity_id
        json metadata
        timestamp created_at
    }
    
    API_KEYS {
        uuid id PK
        uuid tenant_id FK
        string name
        string hashed_key
        json scopes
        timestamp created_at
    }
```

### Data Flow Pipeline

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'clusterBkg': 'transparent', 'clusterBorder': '#ffffff', 'edgeLabelBackground': 'transparent'}}}%%
graph LR
    subgraph "Operational Data"
        OLTP[PostgreSQL OLTP<br/>Reviews, Findings, Users]
    end
    
    subgraph "ETL Pipeline"
        EXTRACT[Daily Export Job<br/>analytics_export.py]
        VALIDATE[Great Expectations<br/>Data Quality Checks]
    end
    
    subgraph "Analytics Storage"
        PARQUET[Parquet Files<br/>Partitioned by date<br/>s3 analytics findings dt 2024-01-15]
        DELTA[Delta Lake<br/>ACID transactions<br/>Time travel queries]
    end
    
    subgraph "Analytics Compute"
        SPARK[PySpark Notebooks<br/>KPI Calculations<br/>Trend Analysis]
        JUPYTER[Jupyter Lab<br/>Ad-hoc Analysis]
    end
    
    subgraph "Business Intelligence"
        DASHBOARDS[Grafana Dashboards<br/>Real-time Metrics]
        REPORTS[Weekly Reports<br/>Executive Summaries]
    end
    
    OLTP --> EXTRACT
    EXTRACT --> VALIDATE
    VALIDATE --> PARQUET
    VALIDATE --> DELTA
    PARQUET --> SPARK
    DELTA --> SPARK
    SPARK --> JUPYTER
    SPARK --> DASHBOARDS
    DASHBOARDS --> REPORTS
    
    style OLTP fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style EXTRACT fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style VALIDATE fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style PARQUET fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DELTA fill:#1abc9c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style SPARK fill:#e67e22,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style JUPYTER fill:#27ae60,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DASHBOARDS fill:#2ecc71,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style REPORTS fill:#34495e,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

## Security Architecture

### Authentication & Authorization Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'clusterBkg': 'transparent', 'clusterBorder': '#ffffff', 'edgeLabelBackground': 'transparent'}}}%%
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        API_CLIENT[API Client]
        WEBHOOK[GitHub Webhook]
    end
    
    subgraph "Security Gateway"
        WAF[Web Application Firewall<br/>Rate Limiting<br/>DDoS Protection]
        TLS[TLS 1.3 Termination<br/>Certificate Management]
    end
    
    subgraph "Authentication Layer"
        JWT_DECODE[JWT Token Decoder<br/>RS256 Algorithm]
        GITHUB_OAUTH[GitHub OAuth<br/>App Installation]
        WEBHOOK_SIG[Webhook Signature<br/>HMAC-SHA256]
    end
    
    subgraph "Authorization Layer"
        RBAC_ENGINE[RBAC Engine<br/>Role Hierarchy<br/>Viewer to Owner]
        TENANT_ISOLATION[Tenant Isolation<br/>Multi-tenancy Enforcement]
        RATE_LIMITER[Rate Limiter<br/>Token Bucket per Tenant]
    end
    
    subgraph "Application Layer"
        API[FastAPI Application<br/>Business Logic]
        DB[PostgreSQL<br/>Row-Level Security]
    end
    
    WEB --> WAF
    API_CLIENT --> WAF
    WEBHOOK --> TLS
    
    WAF --> JWT_DECODE
    TLS --> WEBHOOK_SIG
    
    JWT_DECODE --> RBAC_ENGINE
    GITHUB_OAUTH --> RBAC_ENGINE
    WEBHOOK_SIG --> API
    
    RBAC_ENGINE --> TENANT_ISOLATION
    TENANT_ISOLATION --> RATE_LIMITER
    RATE_LIMITER --> API
    
    API --> DB
    
    style WEB fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style API_CLIENT fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style WEBHOOK fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style WAF fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style TLS fill:#e67e22,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style JWT_DECODE fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style GITHUB_OAUTH fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style WEBHOOK_SIG fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style RBAC_ENGINE fill:#27ae60,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style TENANT_ISOLATION fill:#2ecc71,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style RATE_LIMITER fill:#1abc9c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style API fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style DB fill:#34495e,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

### Security Controls Matrix

| Layer | Control | Implementation | Purpose |
|-------|---------|----------------|---------|
| **Network** | TLS 1.3 | Nginx/ALB termination | Data in transit |
| **Network** | WAF Rules | AWS WAF / ModSecurity | Attack prevention |
| **API** | Rate Limiting | Token bucket (100/min) | DoS prevention |
| **API** | Input Validation | Pydantic models | Injection prevention |
| **Auth** | JWT Tokens | RS256 signing | Stateless auth |
| **Auth** | RBAC | 4-tier role hierarchy | Principle of least privilege |
| **Data** | Encryption at Rest | PostgreSQL TDE | Data confidentiality |
| **Data** | Row-Level Security | Tenant isolation | Multi-tenancy |
| **App** | Secret Management | Environment variables | Credential security |
| **App** | Dependency Scanning | pip-audit, npm audit | Supply chain security |

## Scalability & Performance

### Horizontal Scaling Strategy

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'clusterBkg': 'transparent', 'clusterBorder': '#ffffff', 'edgeLabelBackground': 'transparent'}}}%%
graph TB
    subgraph "Load Distribution"
        ALB[Application Load Balancer<br/>Round Robin with Health Checks]
        ASG[Auto Scaling Group<br/>2 to 10 API instances]
    end
    
    subgraph "API Tier Scaling"
        API1[FastAPI Pod 1<br/>Requests: 0.25 CPU<br/>Limits: 0.5 CPU]
        API2[FastAPI Pod 2<br/>Memory: 256Mi<br/>Limits: 512Mi]
        APIN[FastAPI Pod N<br/>HPA Target: 70% CPU]
    end
    
    subgraph "Worker Tier Scaling"
        KEDA[KEDA Scaler<br/>Redis Queue Length<br/>Scale 1 to 20 workers]
        W1[Security Worker<br/>CPU Intensive<br/>2 CPU and 4GB]
        W2[Style Worker<br/>I/O Light<br/>1 CPU and 2GB]
        WN[Worker Pool<br/>Queue-based scaling]
    end
    
    subgraph "Data Tier Scaling"
        PGPRIMARY[PostgreSQL Primary<br/>Write scaling<br/>Connection pooling]
        PGREPLICA1[Read Replica 1<br/>Analytics queries]
        PGREPLICA2[Read Replica 2<br/>Reporting queries]
        REDIS_CLUSTER[Redis Cluster<br/>6 nodes total<br/>3 primary and 3 replica]
    end
    
    ALB --> ASG
    ASG --> API1
    ASG --> API2
    ASG --> APIN
    
    API1 --> KEDA
    KEDA --> W1
    KEDA --> W2
    KEDA --> WN
    
    API1 --> PGPRIMARY
    API2 --> PGREPLICA1
    APIN --> PGREPLICA2
    
    W1 --> REDIS_CLUSTER
    W2 --> REDIS_CLUSTER
    WN --> REDIS_CLUSTER
    
    style ALB fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style ASG fill:#2980b9,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style API1 fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style API2 fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style APIN fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style KEDA fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style W1 fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style W2 fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style WN fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style PGPRIMARY fill:#27ae60,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style PGREPLICA1 fill:#2ecc71,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style PGREPLICA2 fill:#2ecc71,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style REDIS_CLUSTER fill:#e67e22,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

### Performance Optimization Techniques

| Component | Optimization | Implementation | Impact |
|-----------|-------------|----------------|---------|
| **API** | Connection Pooling | SQLAlchemy pool (20 connections) | 40% latency reduction |
| **API** | Response Caching | Redis TTL cache (1h) | 60% cache hit rate |
| **API** | Async Processing | Celery task queue | Non-blocking webhook responses |
| **Database** | Query Optimization | Indexed queries, EXPLAIN plans | 200ms → 45ms average |
| **Database** | Read Replicas | Separate analytics traffic | Primary DB load -35% |
| **Queue** | Batch Processing | Process multiple findings together | 25% throughput increase |
| **Workers** | Resource Allocation | CPU/memory tuned per agent type | Optimal resource utilization |

## Technology Decisions

### Backend Framework: FastAPI

**Why FastAPI over alternatives?**

| Criteria | FastAPI | Django REST | Flask |
|----------|---------|-------------|-------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Type Safety** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Auto Documentation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Async Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Learning Curve** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Decision**: FastAPI chosen for superior performance, built-in OpenAPI docs, and excellent async support needed for webhook processing.

### Task Queue: Celery + Redis

**Why Celery over alternatives?**

- **Proven Scalability**: Battle-tested in high-throughput environments
- **Rich Ecosystem**: Comprehensive monitoring, routing, and retry mechanisms  
- **Redis Backend**: Fast, reliable message broker with persistence
- **Flexible Routing**: Different queues for different agent types
- **KEDA Integration**: Kubernetes-native autoscaling based on queue depth

### Database: PostgreSQL

**Why PostgreSQL over alternatives?**

- **ACID Compliance**: Critical for financial/audit data
- **JSON Support**: Native JSONB for flexible agent metrics storage
- **Full-Text Search**: Built-in search capabilities for code content
- **Row-Level Security**: Native multi-tenancy support
- **Rich Ecosystem**: Excellent ORM support, monitoring tools

### Frontend: React + TypeScript

**Technology Rationale**:
- **React**: Large talent pool, mature ecosystem
- **TypeScript**: Type safety reduces runtime errors by 60%
- **Material-UI**: Consistent, accessible design system
- **React Query**: Intelligent caching and synchronization

## Deployment Architecture

### Kubernetes Production Setup

```yaml
# Kubernetes Cluster Layout
apiVersion: v1
kind: Namespace
metadata:
  name: ai-code-review-prod
---
# Example resource allocation
resources:
  backend:
    replicas: 3
    cpu: "500m"
    memory: "1Gi"
    limits:
      cpu: "1000m" 
      memory: "2Gi"
  workers:
    replicas: 2-10  # KEDA auto-scaling
    cpu: "250m"
    memory: "512Mi"
  frontend:
    replicas: 2
    cpu: "100m"
    memory: "128Mi"
```

### Infrastructure as Code

```hcl
# Terraform AWS Infrastructure
module "eks_cluster" {
  source = "./modules/eks"
  
  cluster_name     = "ai-code-review-prod"
  node_groups = {
    main = {
      instance_types = ["m5.large"]
      min_size      = 2
      max_size      = 10
      desired_size  = 3
    }
  }
}

module "rds_postgres" {
  source = "./modules/rds"
  
  engine_version    = "15.4"
  instance_class    = "db.r6g.large"
  allocated_storage = 500
  backup_retention  = 7
  multi_az         = true
}

module "elasticache_redis" {
  source = "./modules/elasticache"
  
  node_type         = "cache.r6g.large"
  num_cache_nodes   = 3
  parameter_group   = "redis7.x"
}
```

### Monitoring & Observability Stack

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': 'transparent', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#ffffff', 'lineColor': '#ffffff', 'secondaryColor': 'transparent', 'tertiaryColor': 'transparent', 'background': 'transparent', 'mainBkg': 'transparent', 'secondBkg': 'transparent', 'tertiaryBkg': 'transparent', 'clusterBkg': 'transparent', 'clusterBorder': '#ffffff', 'edgeLabelBackground': 'transparent'}}}%%
graph TB
    subgraph "Metrics Collection"
        PROM[Prometheus<br/>Metrics scraping<br/>15s intervals]
        CADVISOR[cAdvisor<br/>Container metrics]
        NODE_EXP[Node Exporter<br/>System metrics]
    end
    
    subgraph "Distributed Tracing"
        JAEGER[Jaeger<br/>Request tracing<br/>Performance analysis]
        OTEL[OpenTelemetry<br/>Auto-instrumentation<br/>FastAPI SQLAlchemy Celery]
    end
    
    subgraph "Log Management"
        FLUENT[Fluent Bit<br/>Log collection]
        ELASTICSEARCH[Elasticsearch<br/>Log storage and search]
        KIBANA[Kibana<br/>Log visualization]
    end
    
    subgraph "Alerting & Dashboards"
        GRAFANA[Grafana<br/>Dashboards and Alerts]
        ALERTMANAGER[AlertManager<br/>Alert routing]
        PAGERDUTY[PagerDuty<br/>Incident management]
        SLACK[Slack<br/>Team notifications]
    end
    
    PROM --> GRAFANA
    CADVISOR --> PROM
    NODE_EXP --> PROM
    
    JAEGER --> GRAFANA
    OTEL --> JAEGER
    
    FLUENT --> ELASTICSEARCH
    ELASTICSEARCH --> KIBANA
    
    GRAFANA --> ALERTMANAGER
    ALERTMANAGER --> PAGERDUTY
    ALERTMANAGER --> SLACK
    
    style PROM fill:#e74c3c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style CADVISOR fill:#e67e22,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style NODE_EXP fill:#f39c12,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style JAEGER fill:#9b59b6,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style OTEL fill:#8e44ad,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style FLUENT fill:#3498db,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style ELASTICSEARCH fill:#2980b9,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style KIBANA fill:#21618c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    style GRAFANA fill:#27ae60,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style ALERTMANAGER fill:#2ecc71,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style PAGERDUTY fill:#1abc9c,stroke:#ffffff,stroke-width:3px,color:#ffffff
    style SLACK fill:#16a085,stroke:#ffffff,stroke-width:3px,color:#ffffff
```

### Disaster Recovery Strategy

| Component | RPO | RTO | Strategy |
|-----------|-----|-----|----------|
| **PostgreSQL** | 5 minutes | 15 minutes | Streaming replication + PITR |
| **Redis** | 1 minute | 5 minutes | AOF persistence + backup |
| **Application** | 0 seconds | 2 minutes | Stateless, rolling deployments |
| **Analytics Data** | 24 hours | 1 hour | S3 cross-region replication |

---

## Performance Benchmarks

### Load Testing Results

```bash
# Locust load test @ 20 RPS
Total requests: 12,000
Average response time: 220ms
95th percentile: 450ms  
99th percentile: 680ms
Error rate: 0.02%

# Queue processing throughput
Average PR processing time: 45 seconds
Peak queue throughput: 15 PRs/minute
Worker utilization: 73% average
```

### Scalability Targets

| Metric | Current | Target (6 months) | Strategy |
|--------|---------|-------------------|----------|
| **Concurrent Users** | 100 | 1,000 | Horizontal API scaling |
| **PRs per day** | 500 | 5,000 | Worker pool expansion |
| **API latency p95** | 220ms | <200ms | Query optimization |
| **Queue processing** | 45s | <30s | Agent optimization |

This architecture supports our growth trajectory from startup to enterprise scale, with clear paths for optimization and expansion at each tier.
