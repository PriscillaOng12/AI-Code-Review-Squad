# API Reference

The REST API is implemented using FastAPI and documented via OpenAPI/Swagger at `/docs`.  This file summarises the primary endpoints and their expected inputs and outputs.  All endpoints require authentication via a JWT returned from the OIDC login flow, except for webhooks which authenticate via GitHub signatures.

## Authentication

### `GET /api/auth/login`

Initiates the GitHub OIDC login flow.  The user is redirected to GitHub to authorise the application.  Upon success, a signed JWT is returned to the frontend for subsequent API calls.

### `POST /api/auth/logout`

Revokes the current session and clears cookies.  Requires a valid JWT.

## Webhooks

### `POST /api/webhooks/github`

Handles GitHub webhook events.  The signature is verified using the `GITHUB_WEBHOOK_SECRET`.  Supports `pull_request` events with actions `opened`, `synchronize` and `reopened`.  The body must be the raw JSON payload from GitHub.  Returns 200 on acceptance.  Idempotency keys are used to prevent duplicate processing.

## Reviews

### `GET /api/reviews`

Returns a paginated list of reviews accessible to the current user.  Query parameters:

| Parameter    | Type     | Description                           |
|--------------|----------|---------------------------------------|
| `limit`      | integer  | Max number of reviews to return       |
| `offset`     | integer  | Offset for pagination                 |
| `status`     | string   | Filter by status (`pending`, `running`, `completed`, `failed`) |
| `repo_id`    | UUID     | Filter by repository                  |

Response body is an array of `Review` objects with metadata and aggregated statistics.

### `GET /api/reviews/{review_id}`

Returns the details of a single review including associated agent runs and aggregated finding counts.  Requires access via RBAC.

## Findings

### `GET /api/reviews/{review_id}/findings`

Lists all findings for a given review.  Supports filtering by agent name, severity (`critical`, `high`, `medium`, `low`, `info`), file path and pagination.  Returns a JSON array of finding objects.

## Export

### `GET /api/exports/reviews/{review_id}/sarif`

Returns a SARIF (Static Analysis Results Interchange Format) document representing the findings for the review.  This can be uploaded directly to GitHub to display security findings in the Security tab.

### `GET /api/exports/reviews/{review_id}/comments`

Returns a Markdown document containing the recommendations for each finding.  The frontend uses this to post comments to the pull request.

## Admin & Analytics

### `POST /api/admin/analytics/export`

Triggers a manual export of analytics data for a given date.  Accepts a query parameter `date` formatted as `YYYY-MM-DD`.  Requires the requester to have the `Owner` role.  See `docs/ANALYTICS.md` for details.

### `GET /api/exports/analytics/latest-manifest`

Returns the latest available manifests for the analytics tables.  The response contains URIs to the Parquet/Delta files for each table and date partition.  The frontend uses this to display download links.

## Errors

All error responses follow a consistent structure:

```
{
  "detail": "error message",
  "code": "ERROR_CODE"
}
```

For example, a 403 Forbidden error due to insufficient permissions returns `{"detail":"Forbidden","code":"FORBIDDEN"}`.

Refer to the generated OpenAPI specification for detailed schemas and example responses.