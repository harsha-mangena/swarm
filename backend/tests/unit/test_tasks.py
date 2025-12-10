"""Unit tests for task persistence"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models.task import Task, TaskStatus, CreateTaskRequest


class TestTaskModels:
    """Test task models"""
    
    def test_task_creation(self):
        """Test creating a task with defaults"""
        task = Task(
            description="Test task",
            provider="auto"
        )
        assert task.id is not None
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.provider == "auto"
        assert task.subtasks == []
        assert task.agents_count == 0
    
    def test_task_with_all_fields(self):
        """Test creating a task with all fields"""
        task = Task(
            id="test-123",
            description="Full test task",
            status=TaskStatus.COMPLETED,
            provider="google",
            result={"content": "Test result"},
            agents_count=3,
            progress=1.0,
            subtasks=[{"id": "sub-1", "status": "completed"}],
            validation_results={"summary": "Validated"},
        )
        assert task.id == "test-123"
        assert task.status == TaskStatus.COMPLETED
        assert task.agents_count == 3
        assert len(task.subtasks) == 1


class TestCreateTaskRequest:
    """Test CreateTaskRequest model"""
    
    def test_default_values(self):
        """Test default values for CreateTaskRequest"""
        request = CreateTaskRequest(description="Test")
        assert request.description == "Test"
        assert request.provider == "auto"
        assert request.auto_execute is True
        assert request.context is None
    
    def test_custom_values(self):
        """Test custom values for CreateTaskRequest"""
        request = CreateTaskRequest(
            description="Custom task",
            provider="anthropic",
            auto_execute=False,
            context={"key": "value"}
        )
        assert request.provider == "anthropic"
        assert request.auto_execute is False
        assert request.context == {"key": "value"}


class TestTaskStatus:
    """Test TaskStatus enum"""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist"""
        statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.VALIDATING,
            TaskStatus.DEBATING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]
        assert len(statuses) == 7
    
    def test_status_values(self):
        """Test status string values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"


@pytest.fixture
def mock_postgres_store():
    """Create a mock PostgresMemoryStore"""
    store = AsyncMock()
    store.save_task = AsyncMock()
    store.get_task = AsyncMock(return_value=None)
    store.list_tasks = AsyncMock(return_value=[])
    store.delete_task = AsyncMock(return_value=True)
    return store


@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        id="test-task-123",
        description="Sample test task",
        status=TaskStatus.PENDING,
        provider="auto",
    )


class TestTaskPersistence:
    """Test task persistence functions"""
    
    @pytest.mark.asyncio
    async def test_save_task_to_db(self, mock_postgres_store, sample_task):
        """Test saving a task to database"""
        from backend.api.routes.tasks import save_task_to_db
        
        await save_task_to_db(sample_task, mock_postgres_store)
        
        mock_postgres_store.save_task.assert_called_once()
        call_args = mock_postgres_store.save_task.call_args[0][0]
        assert call_args["id"] == "test-task-123"
        assert call_args["description"] == "Sample test task"
        assert call_args["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_save_task_to_db_handles_none_store(self, sample_task):
        """Test saving with None postgres store doesn't raise"""
        from backend.api.routes.tasks import save_task_to_db
        
        # Should not raise
        await save_task_to_db(sample_task, None)
    
    @pytest.mark.asyncio
    async def test_save_task_to_db_handles_error(self, mock_postgres_store, sample_task):
        """Test saving handles store errors gracefully"""
        from backend.api.routes.tasks import save_task_to_db
        
        mock_postgres_store.save_task.side_effect = Exception("DB error")
        
        # Should not raise, just log warning
        await save_task_to_db(sample_task, mock_postgres_store)
