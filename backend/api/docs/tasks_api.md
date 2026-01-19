# MarketplaceTask API Documentation

**API endpoints for querying and monitoring task execution within marketplace jobs**

---

## Overview

The MarketplaceTask API provides endpoints to monitor the granular execution steps within marketplace jobs. Tasks represent atomic operations like "Upload image 1/3" or "Create listing".

**Base Path**: `/api/marketplace/tasks`

**Authentication**: All endpoints require JWT authentication via Bearer token.

---

## Task Model

```json
{
  "id": 789,
  "job_id": 123,
  "task_type": "plugin_http",
  "description": "Upload image 1/3",
  "position": 1,
  "status": "success",
  "payload": {
    "photo_url": "https://r2.stoflow.com/user1/photo1.jpg",
    "photo_order": 1
  },
  "result": {
    "vinted_photo_id": 456,
    "url": "https://images.vinted.net/...",
    "uploaded_at": "2026-01-16T10:01:15Z"
  },
  "error_message": null,
  "product_id": 456,
  "platform": "vinted",
  "http_method": "POST",
  "path": "/api/v2/photos",
  "retry_count": 0,
  "started_at": "2026-01-16T10:00:20Z",
  "completed_at": "2026-01-16T10:01:15Z",
  "created_at": "2026-01-16T10:00:15Z"
}
```

**Task Types**:
- `plugin_http`: HTTP request via browser plugin (Vinted DataDome bypass)
- `direct_http`: Direct HTTP request from backend (eBay, Etsy, CDN)
- `db_operation`: Database operation
- `file_operation`: File upload/download (R2, S3)

**Status Values**:
- `pending`: Waiting for execution
- `processing`: Currently being executed
- `success`: Successfully completed
- `failed`: Execution failed
- `timeout`: Execution timed out
- `cancelled`: Cancelled by user

---

## Endpoints

### GET /api/marketplace/tasks

List tasks with filters and pagination.

**Query Parameters**:
- `job_id` (integer, optional): Filter by parent job
- `status` (string, optional): Filter by status (pending, processing, success, failed)
- `task_type` (string, optional): Filter by type (plugin_http, direct_http, db_operation, file_operation)
- `limit` (integer, optional): Results per page (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response (200 OK)**:
```json
{
  "tasks": [
    {
      "id": 789,
      "job_id": 123,
      "task_type": "plugin_http",
      "description": "Upload image 1/3",
      "position": 1,
      "status": "success",
      "started_at": "2026-01-16T10:00:20Z",
      "completed_at": "2026-01-16T10:01:15Z",
      "created_at": "2026-01-16T10:00:15Z"
    },
    {
      "id": 790,
      "job_id": 123,
      "task_type": "plugin_http",
      "description": "Upload image 2/3",
      "position": 2,
      "status": "success",
      "started_at": "2026-01-16T10:01:16Z",
      "completed_at": "2026-01-16T10:02:10Z",
      "created_at": "2026-01-16T10:00:15Z"
    }
  ],
  "total": 5,
  "success": 3,
  "failed": 1,
  "pending": 1
}
```

**Example - Get all tasks for a job**:
```bash
curl "http://localhost:8000/api/marketplace/tasks?job_id=123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example - Get failed tasks**:
```bash
curl "http://localhost:8000/api/marketplace/tasks?status=failed&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid authentication token
- `400 Bad Request`: Invalid query parameters

---

### GET /api/marketplace/tasks/{task_id}

Get details of a specific task including payload and result.

**Path Parameters**:
- `task_id` (integer, required): Task ID

**Response (200 OK)**:
```json
{
  "id": 789,
  "job_id": 123,
  "task_type": "plugin_http",
  "description": "Upload image 1/3",
  "position": 1,
  "status": "success",
  "payload": {
    "photo_url": "https://r2.stoflow.com/user1/photo1.jpg",
    "photo_order": 1,
    "orientation": "portrait"
  },
  "result": {
    "vinted_photo_id": 456,
    "url": "https://images.vinted.net/...",
    "uploaded_at": "2026-01-16T10:01:15Z",
    "width": 1200,
    "height": 1600
  },
  "error_message": null,
  "product_id": 456,
  "platform": "vinted",
  "http_method": "POST",
  "path": "/api/v2/photos",
  "retry_count": 0,
  "started_at": "2026-01-16T10:00:20Z",
  "completed_at": "2026-01-16T10:01:15Z",
  "created_at": "2026-01-16T10:00:15Z",
  "job": {
    "id": 123,
    "marketplace": "vinted",
    "action_code": "publish",
    "status": "completed"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Task not found

**Example**:
```bash
curl http://localhost:8000/api/marketplace/tasks/789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Task Execution Details

### Plugin HTTP Tasks (Vinted)

Tasks of type `plugin_http` are executed via WebSocket communication with the browser plugin.

**Flow**:
```
Backend → WebSocket → Frontend → Plugin → Vinted API
        ← WebSocket ← Frontend ← Plugin ← Vinted API
```

**Timeout**: 60 seconds (configurable per task)

**Payload Example**:
```json
{
  "http_method": "POST",
  "path": "/api/v2/items",
  "body": {
    "title": "Nike Air Max 90",
    "price": 29.99,
    "currency": "EUR",
    "category_id": 123
  }
}
```

**Result Example**:
```json
{
  "vinted_id": 987,
  "url": "https://www.vinted.fr/items/987",
  "status": "created",
  "timestamp": "2026-01-16T10:05:30Z"
}
```

### Direct HTTP Tasks (eBay, Etsy)

Tasks of type `direct_http` are executed directly from the backend using httpx.

**Flow**:
```
Backend → httpx → eBay/Etsy API
        ← httpx ← eBay/Etsy API
```

**Timeout**: 30 seconds (default)

**Payload Example**:
```json
{
  "http_method": "POST",
  "path": "https://api.ebay.com/sell/inventory/v1/inventory_item/SKU123",
  "headers": {
    "Authorization": "Bearer ACCESS_TOKEN"
  },
  "body": {
    "product": {
      "title": "Nike Air Max 90"
    }
  }
}
```

**Result Example**:
```json
{
  "sku": "SKU123",
  "status": "PUBLISHED",
  "listing_id": "123456789"
}
```

### Database Operation Tasks

Tasks of type `db_operation` perform database operations.

**Examples**:
- Save listing ID after publication
- Update product status
- Link marketplace product to local product

**Payload Example**:
```json
{
  "operation": "update",
  "table": "vinted_products",
  "where": {"product_id": 456},
  "data": {"vinted_id": 987}
}
```

### File Operation Tasks

Tasks of type `file_operation` handle file uploads/downloads.

**Examples**:
- Upload image to Cloudflare R2
- Download image from external URL
- Generate thumbnail

**Payload Example**:
```json
{
  "operation": "upload",
  "source": "https://example.com/photo.jpg",
  "destination": "r2://bucket/user1/photo1.jpg"
}
```

---

## Task Ordering & Retry Intelligence

### Position Field

Tasks have a `position` field (integer) that determines execution order within a job.

**Example Job with 5 Tasks**:
```
position=1: Validate product data
position=2: Upload image 1/3
position=3: Upload image 2/3
position=4: Upload image 3/3
position=5: Create listing
```

### Retry Behavior

When a job is retried, the processor checks each task's status:

| Task Status | Retry Behavior |
|-------------|----------------|
| `success` | **SKIPPED** (idempotence guarantee) |
| `failed` | **RE-EXECUTED** |
| `pending` | **EXECUTED** |
| `timeout` | **RE-EXECUTED** |
| `cancelled` | **SKIPPED** |

**Example Retry Scenario**:
```
Initial run:
- Task 1 (pos=1): success
- Task 2 (pos=2): success
- Task 3 (pos=3): failed (network error)
- Task 4 (pos=4): pending (never executed)
- Task 5 (pos=5): pending (never executed)

On retry:
- Task 1: SKIPPED (already success)
- Task 2: SKIPPED (already success)
- Task 3: RE-EXECUTED
- Task 4: EXECUTED
- Task 5: EXECUTED
```

---

## Monitoring Task Progress

### Real-Time Polling

To monitor a job's progress in real-time, poll the tasks endpoint:

```javascript
// Frontend polling example
async function monitorJobProgress(jobId) {
  const interval = setInterval(async () => {
    const response = await fetch(
      `http://localhost:8000/api/marketplace/tasks?job_id=${jobId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const data = await response.json();

    console.log(`Progress: ${data.success}/${data.total} tasks completed`);

    // Check if job is done
    if (data.pending === 0 && data.failed === 0) {
      console.log("Job completed successfully!");
      clearInterval(interval);
    } else if (data.failed > 0 && data.pending === 0) {
      console.log("Job failed with errors");
      clearInterval(interval);
    }
  }, 2000); // Poll every 2 seconds
}
```

### Task Progress Calculation

Calculate job progress based on task statuses:

```javascript
function calculateProgress(tasks) {
  const total = tasks.length;
  const completed = tasks.filter(t => t.status === 'success').length;
  const failed = tasks.filter(t => t.status === 'failed').length;
  const pending = tasks.filter(t =>
    t.status === 'pending' || t.status === 'processing'
  ).length;

  return {
    total,
    completed,
    failed,
    pending,
    progress_percent: total > 0 ? (completed / total) * 100 : 0
  };
}
```

---

## Error Handling

### Task Error Message

When a task fails, the `error_message` field contains the error details:

```json
{
  "id": 790,
  "status": "failed",
  "error_message": "DataDome captcha challenge detected",
  "retry_count": 2
}
```

### Common Error Types

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `NetworkError` | Connection failed | Retry task, check plugin connectivity |
| `TimeoutError` | Task exceeded timeout | Increase timeout or optimize operation |
| `ValidationError` | Invalid payload data | Fix payload data before retry |
| `RateLimitError` | API rate limit exceeded | Wait before retrying |
| `AuthenticationError` | Invalid credentials | Refresh OAuth token |

---

## Best Practices

1. **Idempotence**: Design tasks to be idempotent (safe to re-execute)
2. **Granularity**: Keep tasks small and focused (1 task = 1 operation)
3. **Descriptions**: Use clear, human-readable task descriptions
4. **Error Messages**: Log detailed error messages for debugging
5. **Position Order**: Use logical ordering (e.g., upload images before creating listing)
6. **Commit Strategy**: Tasks are committed individually for granular progress tracking
7. **Polling Frequency**: Poll every 2-5 seconds to balance responsiveness and server load

---

*Last Updated: 2026-01-16*
