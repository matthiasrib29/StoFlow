# BatchJob API Documentation

**API endpoints for managing bulk marketplace operations**

---

## Overview

The BatchJob API provides endpoints to create and manage bulk operations across marketplaces. A batch job groups multiple MarketplaceJobs from a single bulk operation (e.g., "Publish 200 products to Vinted").

**Base Path**: `/api/batches`

**Authentication**: All endpoints require JWT authentication via Bearer token.

---

## BatchJob Model

```json
{
  "id": 789,
  "batch_id": "publish_20260116_101530_a1b2c3d4",
  "marketplace": "vinted",
  "action_code": "publish",
  "status": "running",
  "priority": 3,
  "total_count": 200,
  "completed_count": 150,
  "failed_count": 5,
  "cancelled_count": 0,
  "pending_count": 45,
  "progress_percent": 75.0,
  "created_at": "2026-01-16T10:15:30Z",
  "started_at": "2026-01-16T10:15:35Z",
  "completed_at": null,
  "created_by_user_id": 1
}
```

**Status Values**:
- `pending`: Not started yet (no jobs have begun processing)
- `running`: Some jobs are currently running
- `completed`: All jobs completed successfully
- `partially_failed`: Some jobs succeeded, some failed
- `failed`: All jobs failed
- `cancelled`: Batch was cancelled by user

**Progress Calculation**:
- `progress_percent = (completed_count / total_count) * 100`
- `pending_count = total_count - (completed_count + failed_count + cancelled_count)`

---

## Endpoints

### POST /api/batches

Create a new batch job with multiple marketplace jobs.

**Request Body**:
```json
{
  "marketplace": "vinted",
  "action_code": "publish",
  "product_ids": [123, 456, 789, 101, 112],
  "priority": 3
}
```

**Field Descriptions**:
- `marketplace` (string, required): Target marketplace (vinted, ebay, etsy)
- `action_code` (string, required): Action to perform (publish, update, delete, link_product, sync)
- `product_ids` (array of integers, required): List of product IDs (min: 1 product)
- `priority` (integer, optional): Priority override (1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW)

**Response (201 Created)**:
```json
{
  "id": 789,
  "batch_id": "publish_20260116_101530_a1b2c3d4",
  "marketplace": "vinted",
  "action_code": "publish",
  "total_count": 5,
  "status": "pending",
  "priority": 3,
  "created_at": "2026-01-16T10:15:30Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid marketplace, action_code, or empty product_ids
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: One or more products not found

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/batches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "vinted",
    "action_code": "publish",
    "product_ids": [123, 456, 789],
    "priority": 2
  }'
```

---

### GET /api/batches/{batch_id}

Get detailed status and progress of a batch job.

**Path Parameters**:
- `batch_id` (integer, required): Batch job ID

**Response (200 OK)**:
```json
{
  "id": 789,
  "batch_id": "publish_20260116_101530_a1b2c3d4",
  "marketplace": "vinted",
  "action_code": "publish",
  "status": "running",
  "priority": 3,
  "total_count": 200,
  "completed_count": 150,
  "failed_count": 5,
  "cancelled_count": 0,
  "pending_count": 45,
  "progress_percent": 75.0,
  "created_at": "2026-01-16T10:15:30Z",
  "started_at": "2026-01-16T10:15:35Z",
  "completed_at": null
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Batch not found

**Example**:
```bash
curl http://localhost:8000/api/batches/789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /api/batches

List batch jobs with filters and pagination.

**Query Parameters**:
- `marketplace` (string, optional): Filter by marketplace (vinted, ebay, etsy)
- `status` (string, optional): Filter by status (pending, running, completed, partially_failed, failed, cancelled)
- `limit` (integer, optional): Results per page (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response (200 OK)**:
```json
{
  "batches": [
    {
      "id": 789,
      "batch_id": "publish_20260116_101530_a1b2c3d4",
      "marketplace": "vinted",
      "action_code": "publish",
      "status": "running",
      "total_count": 200,
      "completed_count": 150,
      "progress_percent": 75.0,
      "created_at": "2026-01-16T10:15:30Z"
    },
    {
      "id": 790,
      "batch_id": "update_20260116_112200_b2c3d4e5",
      "marketplace": "ebay",
      "action_code": "update",
      "status": "completed",
      "total_count": 50,
      "completed_count": 50,
      "progress_percent": 100.0,
      "created_at": "2026-01-16T11:22:00Z"
    }
  ],
  "total": 45,
  "active": 12,
  "completed": 28,
  "failed": 5
}
```

**Example - Get active batches**:
```bash
curl "http://localhost:8000/api/batches?status=running&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example - Get all Vinted batches**:
```bash
curl "http://localhost:8000/api/batches?marketplace=vinted" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /api/batches/{batch_id}/cancel

Cancel a batch job and all its pending MarketplaceJobs.

**Path Parameters**:
- `batch_id` (integer, required): Batch job ID to cancel

**Response (200 OK)**:
```json
{
  "id": 789,
  "batch_id": "publish_20260116_101530_a1b2c3d4",
  "status": "cancelled",
  "total_count": 200,
  "completed_count": 150,
  "cancelled_count": 50,
  "message": "Batch cancelled, 50 pending jobs stopped"
}
```

**Behavior**:
1. Sets batch status to `cancelled`
2. Cancels all pending MarketplaceJobs
3. Leaves completed and running jobs untouched
4. Updates progress counters

**Error Responses**:
- `400 Bad Request`: Batch is already in a terminal state (completed, failed, cancelled)
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Batch not found

**Example**:
```bash
curl -X POST http://localhost:8000/api/batches/789/cancel \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /api/batches/{batch_id}/jobs

Get all child MarketplaceJobs for a batch.

**Path Parameters**:
- `batch_id` (integer, required): Batch job ID

**Query Parameters**:
- `status` (string, optional): Filter jobs by status
- `limit` (integer, optional): Results per page (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response (200 OK)**:
```json
{
  "batch_id": "publish_20260116_101530_a1b2c3d4",
  "jobs": [
    {
      "id": 123,
      "product_id": 456,
      "product_title": "Nike Air Max 90",
      "status": "completed",
      "created_at": "2026-01-16T10:15:31Z",
      "completed_at": "2026-01-16T10:20:45Z"
    },
    {
      "id": 124,
      "product_id": 457,
      "product_title": "Adidas Stan Smith",
      "status": "failed",
      "error_message": "Product out of stock",
      "created_at": "2026-01-16T10:15:31Z"
    },
    {
      "id": 125,
      "product_id": 458,
      "product_title": "Reebok Classic",
      "status": "pending",
      "created_at": "2026-01-16T10:15:31Z"
    }
  ],
  "total": 200,
  "page_size": 50,
  "offset": 0
}
```

**Example**:
```bash
# Get all jobs in batch
curl "http://localhost:8000/api/batches/789/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get only failed jobs
curl "http://localhost:8000/api/batches/789/jobs?status=failed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Batch Lifecycle

```
Create Batch (POST /batches)
    ↓
PENDING
    ↓
(first job starts processing)
    ↓
RUNNING
    ↓
    ├─→ (all jobs completed successfully) → COMPLETED
    │
    ├─→ (all jobs failed) → FAILED
    │
    ├─→ (some succeeded, some failed) → PARTIALLY_FAILED
    │
    └─→ (user cancels) → CANCELLED
```

**Terminal States**: COMPLETED, FAILED, PARTIALLY_FAILED, CANCELLED

---

## Status Determination Logic

The batch status is automatically calculated based on child job statuses:

| Condition | Batch Status |
|-----------|--------------|
| No jobs have started | `pending` |
| At least one job is running | `running` |
| All jobs completed successfully | `completed` |
| All jobs failed | `failed` |
| Some jobs succeeded, some failed | `partially_failed` |
| User cancelled the batch | `cancelled` |

**Status Update Triggers**:
- After each MarketplaceJob completes (success or failure)
- When a job is cancelled
- When batch is cancelled via API

---

## Progress Monitoring

### Real-Time Progress Tracking

To monitor batch progress in real-time, poll the batch endpoint:

```javascript
// Frontend polling example
async function monitorBatchProgress(batchId) {
  const interval = setInterval(async () => {
    const response = await fetch(
      `http://localhost:8000/api/batches/${batchId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const batch = await response.json();

    console.log(`Progress: ${batch.progress_percent}%`);
    console.log(`Completed: ${batch.completed_count}/${batch.total_count}`);
    console.log(`Failed: ${batch.failed_count}`);

    // Check if batch is done
    if (batch.status === 'completed') {
      console.log("Batch completed successfully!");
      clearInterval(interval);
    } else if (batch.status === 'failed' || batch.status === 'partially_failed') {
      console.log(`Batch finished with status: ${batch.status}`);
      clearInterval(interval);
    }
  }, 3000); // Poll every 3 seconds
}
```

### Progress Visualization

```javascript
function renderProgressBar(batch) {
  const successPercent = (batch.completed_count / batch.total_count) * 100;
  const failurePercent = (batch.failed_count / batch.total_count) * 100;
  const pendingPercent = (batch.pending_count / batch.total_count) * 100;

  return {
    success: successPercent,
    failure: failurePercent,
    pending: pendingPercent
  };
}
```

---

## Batch Processing Architecture

### Job Priority Queue

Within a batch, jobs are processed in priority order:

```
Priority 1 (CRITICAL) → Processed first
Priority 2 (HIGH)     → Processed second
Priority 3 (NORMAL)   → Processed third
Priority 4 (LOW)      → Processed last
```

Within the same priority, jobs are processed in creation order (FIFO).

### Parallel Processing

Jobs within a batch are processed sequentially by the MarketplaceJobProcessor:

```
Batch with 200 jobs:
Job 1 → Job 2 → Job 3 → ... → Job 200
```

For parallel processing, split into multiple batches or use multiple workers.

### Fault Isolation

Failed jobs do not block other jobs in the batch:

```
Batch: [Job1, Job2, Job3, Job4, Job5]

If Job2 fails:
- Job1: Completed ✅
- Job2: Failed ❌
- Job3: Continues processing
- Job4: Continues processing
- Job5: Continues processing

Batch status: partially_failed
```

---

## Use Cases

### 1. Bulk Product Publishing

```bash
# Publish 500 products to Vinted
curl -X POST http://localhost:8000/api/batches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "vinted",
    "action_code": "publish",
    "product_ids": [1, 2, 3, ..., 500],
    "priority": 3
  }'
```

### 2. Bulk Price Updates

```bash
# Update prices for 200 eBay listings
curl -X POST http://localhost:8000/api/batches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "ebay",
    "action_code": "update",
    "product_ids": [101, 102, ..., 300],
    "priority": 2
  }'
```

### 3. Bulk Product Sync

```bash
# Sync 1000 products from Etsy
curl -X POST http://localhost:8000/api/batches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "marketplace": "etsy",
    "action_code": "sync",
    "product_ids": [1, 2, ..., 1000],
    "priority": 4
  }'
```

---

## Error Handling

### Batch Creation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `400 Bad Request` | Invalid marketplace or action_code | Use valid values (see documentation) |
| `400 Bad Request` | Empty product_ids array | Provide at least one product ID |
| `404 Not Found` | Product not found | Verify product IDs exist |

### Batch Processing Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Job fails | Invalid product data | Fix product data and retry job |
| Job fails | Rate limit exceeded | Wait and retry later |
| Job fails | Marketplace API error | Check marketplace status |

### Handling Partially Failed Batches

```javascript
async function handlePartiallyFailedBatch(batchId) {
  // Get batch details
  const batch = await fetch(`/api/batches/${batchId}`);

  if (batch.status === 'partially_failed') {
    // Get failed jobs
    const failedJobs = await fetch(
      `/api/batches/${batchId}/jobs?status=failed`
    );

    // Retry failed jobs individually
    for (const job of failedJobs.jobs) {
      await fetch(`/api/marketplace/jobs/${job.id}/retry`, {
        method: 'POST'
      });
    }
  }
}
```

---

## Best Practices

1. **Batch Size**: Keep batches under 1000 jobs for optimal performance
2. **Polling Frequency**: Poll every 3-5 seconds to balance responsiveness and server load
3. **Error Handling**: Check `partially_failed` status and retry failed jobs
4. **Priority Management**: Use priority 1-2 only for time-sensitive batches
5. **Cancellation**: Cancel batches early if no longer needed to free resources
6. **Monitoring**: Track `failed_count` and investigate common failure patterns

---

*Last Updated: 2026-01-16*
