# API Documentation

## Overview

The AI Code Review Squad API provides a comprehensive set of endpoints for managing repositories, code reviews, and agent findings. This REST API is built with FastAPI and follows OpenAPI 3.0 specifications.

## Base URL

```
Production: https://api.ai-code-review-squad.com
Staging: https://staging-api.ai-code-review-squad.com
Development: http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

## Core Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout user

### Repositories
- `GET /repositories` - List user repositories
- `POST /repositories` - Add repository
- `GET /repositories/{id}` - Get repository details
- `PUT /repositories/{id}` - Update repository
- `DELETE /repositories/{id}` - Remove repository
- `POST /repositories/{id}/sync` - Sync with GitHub

### Reviews
- `GET /reviews` - List reviews
- `POST /reviews` - Create new review
- `GET /reviews/{id}` - Get review details
- `GET /reviews/{id}/findings` - Get review findings
- `POST /reviews/{id}/rerun` - Rerun review

### Webhooks
- `POST /webhooks/github` - GitHub webhook endpoint
- `GET /webhooks/status` - Webhook status

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Data Models

### Repository

```json
{
  "id": 1,
  "name": "my-project",
  "full_name": "username/my-project",
  "github_id": 123456789,
  "owner_id": 1,
  "is_active": true,
  "webhook_id": 98765,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Review

```json
{
  "id": 1,
  "repository_id": 1,
  "pr_number": 42,
  "commit_sha": "abc123def456",
  "status": "completed",
  "total_findings": 15,
  "risk_score": 3.2,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

### Finding

```json
{
  "id": 1,
  "review_id": 1,
  "agent_name": "security-agent",
  "title": "Potential SQL Injection",
  "description": "Direct string concatenation in SQL query",
  "severity": "high",
  "confidence": 0.85,
  "category": "security",
  "rule_id": "SEC-001",
  "file_path": "src/models/user.py",
  "line_number": 45,
  "code_snippet": "query = \"SELECT * FROM users WHERE id = \" + user_id",
  "suggestion": "Use parameterized queries to prevent SQL injection",
  "created_at": "2024-01-15T10:32:00Z",
  "updated_at": "2024-01-15T10:32:00Z"
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Free tier**: 100 requests per hour
- **Pro tier**: 1,000 requests per hour
- **Enterprise**: 10,000 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Invalid input data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

## Examples

### Creating a Review

```bash
curl -X POST https://api.ai-code-review-squad.com/reviews \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": 1,
    "pr_number": 42,
    "commit_sha": "abc123def456"
  }'
```

### Getting Review Results

```bash
curl -X GET https://api.ai-code-review-squad.com/reviews/1/findings \
  -H "Authorization: Bearer your-jwt-token"
```

## SDKs and Libraries

- **Python**: `pip install ai-code-review-client`
- **JavaScript**: `npm install @ai-code-review/client`
- **Go**: `go get github.com/ai-code-review/go-client`

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- Production: https://api.ai-code-review-squad.com/docs
- Interactive docs: https://api.ai-code-review-squad.com/redoc

## Support

For API support and questions:
- Documentation: https://docs.ai-code-review-squad.com
- GitHub Issues: https://github.com/yourusername/ai-code-review-squad/issues
- Email: api-support@ai-code-review-squad.com
