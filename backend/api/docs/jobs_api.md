# MarketplaceJob API Documentation

**API endpoints for managing marketplace jobs across Vinted, eBay, and Etsy**

---

## Overview

The MarketplaceJob API provides endpoints to create, monitor, and manage individual marketplace operations. Jobs represent single operations (publish, update, delete, sync) on products or marketplace data.

**Base Path**: `/api/marketplace/jobs` (for generic endpoints) or `/api/{marketplace}/jobs` (for marketplace-specific endpoints)

**Authentication**: All endpoints require JWT authentication via Bearer token.

---

## Job Model

```json
{
  "id": 123,
  "marketplace": "vinted",
  "action_type_id": 5,
  "action_code": "publish",
  "action_name": "Publish to Vinted",
  "product_id": 456,
  "product_title": "Nike Air Max 90",
  "batch_id": "publish_20260116_a1b2c3d4",
  "batch_job_id": 789,
  "status": "completed",
  "priority": 3,
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3,
  "input_data": {
    "override_price": 29.99
  },
  "result_data": {
    "vinted_id": 987,
    "url": "https://www.vinted.fr/items/987"
  },
  "started_at": "2026-01-16T10:00:15Z",
  "completed_at": "2026-01-16T10:05:30Z",
  "expires_at": "2026-01-16T11:00:00Z",
  "created_at": "2026-01-16T10:00:00Z"
}
```

**Status Values**:
- `pending`: Waiting to be processed
- `running`: Currently being processed
- `paused`: Paused by user, can be resumed
- `completed`: Successfully completed
- `failed`: Failed after max retries
- `cancelled`: Cancelled by user
- `expired`: Expired (pending > 1 hour)

**Priority Values**:
- `1`: CRITICAL (processed first)
- `2`: HIGH
- `3`: NORMAL (default)
- `4`: LOW

---

## Endpoints

### POST /api/marketplace/jobs

Create a new marketplace job.

**Request Body**:
```json
{
  "marketplace": "vinted",
  "action_code": "publish",
  "product_id": 456,
  "batch_job_id": null,
  "priority": 3,
  "input_data": {
    "override_price": 29.99,
    "custom_description": "Special description"
  }
}
```

**Response (201 Created)**:
```json
{
  "id": 123,
  "marketplace": "vinted",
  "action_code": "publish",
  "action_name": "Publish to Vinted",
  "product_id": 456,
  "status": "pending",
  "priority": 3,
  "created_at": "2026-01-16T10:00:00Z",
  "expires_at": "2026-01-16T11:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid marketplace or action_code
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Product not found

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/marketplace/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "vinted",
    "action_code": "publish",
    "product_id": 456,
    "priority": 2
  }'
```

---

### GET /api/marketplace/jobs/{job_id}

Get details of a specific job including tasks.

**Path Parameters**:
- `job_id` (integer, required): Job ID

**Response (200 OK)**:
```json
{
  "id": 123,
  "marketplace": "vinted",
  "action_code": "publish",
  "action_name": "Publish to Vinted",
  "product_id": 456,
  "product_title": "Nike Air Max 90",
  "status": "completed",
  "priority": 3,
  "retry_count": 0,
  "error_message": null,
  "started_at": "2026-01-16T10:00:15Z",
  "completed_at": "2026-01-16T10:05:30Z",
  "created_at": "2026-01-16T10:00:00Z",
  "tasks": [
    {
      "id": 789,
      "task_type": "plugin_http",
      "description": "Upload image 1/3",
      "position": 1,
      "status": "success",
      "started_at": "2026-01-16T10:00:20Z",
      "completed_at": "2026-01-16T10:01:15Z"
    },
    {
      "id": 790,
      "task_type": "plugin_http",
      "description": "Upload image 2/3",
      "position": 2,
      "status": "success",
      "started_at": "2026-01-16T10:01:16Z",
      "completed_at": "2026-01-16T10:02:10Z"
    },
    {
      "id": 791,
      "task_type": "plugin_http",
      "description": "Create listing",
      "position": 3,
      "status": "success",
      "started_at": "2026-01-16T10:02:11Z",
      "completed_at": "2026-01-16T10:05:30Z"
    }
  ],
  "progress": {
    "total": 3,
    "completed": 3,
    "failed": 0,
    "pending": 0,
    "progress_percent": 100.0
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Job not found

---

### GET /api/marketplace/jobs

List jobs with filters and pagination.

**Query Parameters**:
- `marketplace` (string, optional): Filter by marketplace (vinted, ebay, etsy)
- `status` (string, optional): Filter by status (pending, running, completed, failed)
- `batch_job_id` (integer, optional): Filter by parent batch
- `limit` (integer, optional): Results per page (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response (200 OK)**:
```json
{
  "jobs": [
    {
      "id": 123,
      "marketplace": "vinted",
      "action_code": "publish",
      "product_id": 456,
      "status": "completed",
      "created_at": "2026-01-16T10:00:00Z"
    },
    {
      "id": 124,
      "marketplace": "ebay",
      "action_code": "update",
      "product_id": 457,
      "status": "pending",
      "created_at": "2026-01-16T10:05:00Z"
    }
  ],
  "total": 250,
  "pending": 45,
  "running": 12,
  "completed": 180,
  "failed": 13
}
```

**Example**:
```bash
# Get pending Vinted jobs
curl "http://localhost:8000/api/marketplace/jobs?marketplace=vinted&status=pending&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /api/marketplace/jobs/{job_id}/retry

Retry a failed job. Skips completed tasks and only re-executes failed tasks.

**Path Parameters**:
- `job_id` (integer, required): Job ID to retry

**Response (200 OK)**:
```json
{
  "id": 123,
  "status": "pending",
  "retry_count": 1,
  "message": "Job queued for retry"
}
```

**Error Responses**:
- `400 Bad Request`: Job is not in FAILED status or max retries exceeded
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Job not found

**Example**:
```bash
curl -X POST http://localhost:8000/api/marketplace/jobs/123/retry \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /api/marketplace/jobs/{job_id}/pause

Pause a running or pending job.

**Path Parameters**:
- `job_id` (integer, required): Job ID to pause

**Response (200 OK)**:
```json
{
  "id": 123,
  "status": "paused",
  "message": "Job paused successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Job is not in PENDING or RUNNING status
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Job not found

---

### POST /api/marketplace/jobs/{job_id}/resume

Resume a paused job.

**Path Parameters**:
- `job_id` (integer, required): Job ID to resume

**Response (200 OK)**:
```json
{
  "id": 123,
  "status": "pending",
  "expires_at": "2026-01-16T12:00:00Z",
  "message": "Job resumed successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Job is not in PAUSED status
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Job not found

---

### POST /api/marketplace/jobs/{job_id}/cancel

Cancel a job and all its pending tasks.

**Path Parameters**:
- `job_id` (integer, required): Job ID to cancel

**Response (200 OK)**:
```json
{
  "id": 123,
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Job is already in a terminal state (completed, failed, cancelled)
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Job not found

---

## Marketplace-Specific Endpoints

### eBay Jobs

**GET /api/ebay/jobs**

List eBay jobs with filters.

Query Parameters: Same as generic endpoint but automatically filtered for `marketplace=ebay`.

**POST /api/ebay/jobs/cancel**

Cancel an eBay job.

Query Parameter: `job_id` (integer, required)

### Vinted Jobs

**GET /api/vinted/jobs**

List Vinted jobs (legacy endpoint, same as generic `/api/marketplace/jobs?marketplace=vinted`).

**POST /api/vinted/jobs/cancel**

Cancel Vinted jobs (can cancel multiple).

---

## Job Lifecycle

```
Create Job (POST /jobs)
    ↓
PENDING → (processor picks up) → RUNNING
    ↓                                ↓
    ↓                            (success)
    ↓                                ↓
    ↓                           COMPLETED
    ↓
    ↓                            (failure, retries available)
    ↓                                ↓
    ↓                           PENDING (retry_count++)
    ↓
    ↓                            (failure, max retries reached)
    ↓                                ↓
    ↓                            FAILED
    ↓
    ↓         (user action: POST /pause)
    ↓                                ↓
    ↓                           PAUSED
    ↓                                ↓
    ↓         (user action: POST /resume)
    ↓                                ↓
    └────────────────────────→ PENDING

    (user action: POST /cancel)
              ↓
         CANCELLED
```

---

## Retry Behavior

When a job is retried (POST /jobs/{id}/retry):

1. **Job-Level Check**: Verify `retry_count < max_retries` (default: 3)
2. **Task-Level Intelligence**:
   - Tasks with `status='success'`: **SKIPPED** (idempotence)
   - Tasks with `status='failed'`: **RE-EXECUTED**
   - Tasks with `status='pending'`: **EXECUTED**
3. **Granular Progress**: Commit after each task completion
4. **Fault Isolation**: Failed task doesn't block others

**Example**:
```
Job has 5 tasks: [SUCCESS, SUCCESS, FAILED, FAILED, PENDING]

On retry:
- Tasks 1-2: Skipped (already completed)
- Tasks 3-4: Re-executed
- Task 5: Executed for the first time
```

---

## Rate Limiting

Jobs are processed with rate limiting per marketplace:
- **Vinted**: 10 jobs/minute (WebSocket limited by plugin)
- **eBay**: 5000 calls/day (API rate limit)
- **Etsy**: 10000 calls/day (API rate limit)

---

## Best Practices

1. **Batch Operations**: Use `/api/batches` endpoint for multiple products instead of creating individual jobs
2. **Monitor Progress**: Poll `/api/marketplace/jobs/{id}` for real-time progress updates
3. **Handle Failures**: Check `error_message` field for debugging failed jobs
4. **Retry Strategy**: Wait before retrying to avoid rate limits
5. **Priority Management**: Use priority 1-2 for time-sensitive operations only

---

*Last Updated: 2026-01-16*
