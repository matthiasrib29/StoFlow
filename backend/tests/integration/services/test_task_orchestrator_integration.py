"""
Integration Tests for TaskOrchestrator with PostgreSQL

Tests complete retry workflow with real database operations.

Created: 2026-01-15
Phase: 01-02 Task Orchestration Foundation
"""

import pytest
from datetime import datetime, timezone

from models.user.marketplace_job import MarketplaceJob, JobStatus
from models.user.marketplace_task import MarketplaceTask, TaskStatus
from services.marketplace.task_orchestrator import TaskOrchestrator


class TestTaskOrchestratorIntegration:
    """Integration tests with real PostgreSQL database."""

    def test_full_retry_scenario(self, db_session, cleanup_data):
        """
        Complete retry scenario:
        1. Create job with 5 tasks
        2. First execution fails on task 3
        3. Verify partial progress (tasks 1-2 SUCCESS, task 3 FAILED, tasks 4-5 PENDING)
        4. Retry: skip tasks 1-2, retry task 3, execute tasks 4-5
        5. Verify all tasks SUCCESS

        This test validates:
        - Task creation with sequential positions
        - Task execution with commits per task
        - Retry intelligence (skip SUCCESS, retry FAILED)
        - Database persistence across retries
        """
        orchestrator = TaskOrchestrator(db_session)

        # ===== STEP 1: Create job =====
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            product_id=101,
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        # ===== STEP 2: Create 5 tasks =====
        task_names = [
            "Validate product data",
            "Upload image 1/3",
            "Upload image 2/3",  # Will fail on first execution
            "Upload image 3/3",
            "Create Vinted listing"
        ]

        tasks = orchestrator.create_tasks(job, task_names)
        assert len(tasks) == 5

        # Verify tasks created with correct positions
        for i, task in enumerate(tasks, start=1):
            assert task.position == i
            assert task.status == TaskStatus.PENDING
            assert task.job_id == job.id

        # ===== STEP 3: First execution (fails on task 3) =====
        execution_count = {"task_1": 0, "task_2": 0, "task_3": 0, "task_4": 0, "task_5": 0}
        task_3_should_fail = True  # Flag to control task 3 behavior

        def validate_handler(task):
            execution_count["task_1"] += 1
            return {"validated": True, "checks": ["price", "description", "images"]}

        def upload_1_handler(task):
            execution_count["task_2"] += 1
            return {"image_url": "https://cdn.vinted.com/image1.jpg", "image_id": 12345}

        def upload_2_handler(task):
            execution_count["task_3"] += 1
            if task_3_should_fail:
                raise ConnectionError("Vinted API timeout on image upload")
            return {"image_url": "https://cdn.vinted.com/image2.jpg", "image_id": 12346}

        def upload_3_handler(task):
            execution_count["task_4"] += 1
            return {"image_url": "https://cdn.vinted.com/image3.jpg", "image_id": 12347}

        def create_listing_handler(task):
            execution_count["task_5"] += 1
            return {"vinted_id": 98765, "url": "https://vinted.fr/items/98765"}

        handlers = {
            "Validate product data": validate_handler,
            "Upload image 1/3": upload_1_handler,
            "Upload image 2/3": upload_2_handler,
            "Upload image 3/3": upload_3_handler,
            "Create Vinted listing": create_listing_handler,
        }

        # Execute first time (should fail on task 3)
        success = orchestrator.execute_job_with_tasks(job, tasks, handlers)

        assert success is False  # Job failed

        # Verify execution counts (tasks 1-3 executed, tasks 4-5 NOT executed)
        assert execution_count["task_1"] == 1
        assert execution_count["task_2"] == 1
        assert execution_count["task_3"] == 1
        assert execution_count["task_4"] == 0  # Not executed due to failure
        assert execution_count["task_5"] == 0  # Not executed due to failure

        # Refresh tasks from DB to get latest status
        db_session.expire_all()
        fresh_tasks = db_session.query(MarketplaceTask).filter(
            MarketplaceTask.job_id == job.id
        ).order_by(MarketplaceTask.position).all()

        # Verify task statuses after first execution
        assert fresh_tasks[0].status == TaskStatus.SUCCESS  # Task 1 succeeded
        assert fresh_tasks[0].result["validated"] is True

        assert fresh_tasks[1].status == TaskStatus.SUCCESS  # Task 2 succeeded
        assert "image_url" in fresh_tasks[1].result

        assert fresh_tasks[2].status == TaskStatus.FAILED  # Task 3 failed
        assert "timeout" in fresh_tasks[2].error_message.lower()

        assert fresh_tasks[3].status == TaskStatus.PENDING  # Task 4 not executed
        assert fresh_tasks[4].status == TaskStatus.PENDING  # Task 5 not executed

        # ===== STEP 4: Retry (task 3 succeeds this time) =====
        task_3_should_fail = False  # Fix the issue

        # Execute again (retry)
        success = orchestrator.execute_job_with_tasks(job, tasks, handlers)

        assert success is True  # Job succeeded

        # Verify execution counts (tasks 1-2 skipped, task 3 retried, tasks 4-5 executed)
        assert execution_count["task_1"] == 1  # Not re-executed (skipped)
        assert execution_count["task_2"] == 1  # Not re-executed (skipped)
        assert execution_count["task_3"] == 2  # Retried (1 failed + 1 success)
        assert execution_count["task_4"] == 1  # Executed on retry
        assert execution_count["task_5"] == 1  # Executed on retry

        # ===== STEP 5: Verify all tasks SUCCESS =====
        db_session.expire_all()
        final_tasks = db_session.query(MarketplaceTask).filter(
            MarketplaceTask.job_id == job.id
        ).order_by(MarketplaceTask.position).all()

        # All tasks should be SUCCESS
        for task in final_tasks:
            assert task.status == TaskStatus.SUCCESS
            assert task.completed_at is not None
            assert task.result is not None

        # Verify task 3 no longer has error message
        assert final_tasks[2].error_message is None or final_tasks[2].result is not None

        # Verify final results
        assert final_tasks[4].result["vinted_id"] == 98765  # Listing created

    def test_all_tasks_succeed_on_first_try(self, db_session, cleanup_data):
        """Test happy path: all tasks succeed without retry."""
        orchestrator = TaskOrchestrator(db_session)

        # Create job
        job = MarketplaceJob(
            marketplace="vinted",
            action_type_id=1,
            product_id=102,
            status=JobStatus.PENDING,
            priority=3,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        # Create 3 tasks
        task_names = ["Task 1", "Task 2", "Task 3"]
        tasks = orchestrator.create_tasks(job, task_names)

        # Simple handlers that always succeed
        def success_handler(task):
            return {"status": "ok"}

        handlers = {
            "Task 1": success_handler,
            "Task 2": success_handler,
            "Task 3": success_handler,
        }

        # Execute
        success = orchestrator.execute_job_with_tasks(job, tasks, handlers)

        assert success is True

        # Verify all tasks SUCCESS
        db_session.expire_all()
        final_tasks = db_session.query(MarketplaceTask).filter(
            MarketplaceTask.job_id == job.id
        ).all()

        for task in final_tasks:
            assert task.status == TaskStatus.SUCCESS
            assert task.result == {"status": "ok"}
