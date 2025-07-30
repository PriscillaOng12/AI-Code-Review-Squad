# Quick Reference: AI Code Review Squad

## API Endpoints

| Endpoint                | Method | Description                       |
|------------------------|--------|-----------------------------------|
| `/api/review`          | POST   | Submit code for review            |
| `/api/review/{id}`     | GET    | Get review results                |
| `/api/agents`          | GET    | List available agents             |
| `/api/findings`        | GET    | List all findings                 |
| `/api/ws/review/{id}`  | WS     | Real-time review updates (WebSocket) |

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI key
- `ANTHROPIC_API_KEY` - Your Claude key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth

## Setup (Local Dev)

```bash
# 1. Clone and enter repo
git clone https://github.com/your-username/ai-code-review-squad.git
cd ai-code-review-squad

# 2. Set up environment
cp .env.example .env
# (Add your API keys, DB URLs, etc. to .env)

# 3. Start everything (dev mode)
./demo-setup.sh
# or, for full stack:
docker-compose up --build

# 4. Open the dashboard
open demo/dashboard.html
```

## Testing

- **Backend:** `pytest`
- **Frontend:** `npm test` (Jest)
- **E2E:** `npx playwright test`

## Useful Links

- [System Architecture](architecture.md)
- [Agent Implementation](agents.md)
- [Product Thinking](product-thinking.md)
- [API Docs](api.md)
- [Performance Guide](performance.md)
- [Deployment Guide](deployment.md)

---

_This doc is for when you just need the facts, fast!_
