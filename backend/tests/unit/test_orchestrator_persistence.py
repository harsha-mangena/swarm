"""Unit tests for orchestrator persistence checkpoints"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.orchestrator import Orchestrator
from backend.models.task import Task, TaskStatus

class TestOrchestratorPersistence:
    """Test orchestrator persistence"""

    @pytest.mark.asyncio
    async def test_checkpoints_called_during_execution(self):
        """Test that save_task is called multiple times during execution"""
        
        # Mock dependencies
        mock_router = AsyncMock()
        mock_memory = AsyncMock()
        mock_store = AsyncMock()
        mock_memory.postgres_store = mock_store
        
        # Mock delegator and agents
        with patch('backend.core.orchestrator.Delegator') as MockDelegator:
            mock_delegator = MockDelegator.return_value
            mock_delegator.create_delegation_plan = AsyncMock()
            mock_delegator.create_delegation_plan.return_value.dict.return_value = {
                "execution_strategy": "sequential", "agents_needed": []
            }
            mock_delegator.create_delegation_plan.return_value.execution_strategy = "sequential"
            mock_delegator.create_delegation_plan.return_value.agents_needed = []

            # Initialize orchestrator
            orchestrator = Orchestrator(mock_router, mock_memory)
            orchestrator.delegator = mock_delegator
            
            # Mock _create_task_agents to return empty list to simplify
            orchestrator._create_task_agents = AsyncMock(return_value=[])
            orchestrator._run_validation_phase = AsyncMock(return_value={"summary": "ok"})
            orchestrator._synthesize_final_report = AsyncMock(return_value="Final report")
            
            # Create task
            task = Task(id="test-task", description="Test", provider="auto")
            
            # Execute
            await orchestrator.execute_task(task)
            
            # Verify save_task was called multiple times
            # Calls: 
            # 1. IN_PROGRESS start
            # 2. After delegation
            # 3. After subtasks creation
            # 4. (No subtasks loop)
            # 5. VALIDATING start
            # 6. VALIDATING end
            # 7. COMPLETED end
            assert mock_store.save_task.call_count >= 5
            
            # Verify status sequence (last call should be completed)
            args, _ = mock_store.save_task.call_args
            saved_task_dict = args[0]
            assert saved_task_dict['status'] == TaskStatus.COMPLETED
