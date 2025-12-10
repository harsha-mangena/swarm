"""PostgreSQL persistent memory and task storage"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Text, JSON, Integer, DateTime, Float, ForeignKey
from datetime import datetime

from backend.models.memory import MemoryEntry, MemoryScope
from backend.config import settings

Base = declarative_base()


class MemoryRecord(Base):
    """PostgreSQL memory record"""

    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True)
    scope = Column(String, nullable=False)
    namespace = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    entry_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskRecord(Base):
    """PostgreSQL task record"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    provider = Column(String, default="auto")
    context = Column(JSON, default={})
    result = Column(JSON, default={})
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    agents_count = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    debate_state = Column(JSON, default={})
    subtasks = Column(JSON, default=[])
    validation_results = Column(JSON, default={})


class SubTaskRecord(Base):
    """PostgreSQL subtask record"""

    __tablename__ = "subtasks"

    id = Column(String, primary_key=True)
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    agent_id = Column(String, nullable=True)
    agent_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AgentOutputRecord(Base):
    """PostgreSQL agent output record"""

    __tablename__ = "agent_outputs"

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    agent_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    evidence = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class PostgresMemoryStore:
    """Persistent memory and task storage"""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def connect(self):
        """Connect to PostgreSQL"""
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.engine:
            await self.engine.dispose()

    # Memory methods
    async def save(self, entry: MemoryEntry):
        """Save memory entry"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            record = MemoryRecord(
                id=entry.id,
                scope=entry.scope.value,
                namespace=entry.namespace,
                content=entry.content,
                entry_metadata=entry.metadata,
            )
            session.add(record)
            await session.commit()

    async def query(
        self,
        namespace: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Query memory entries"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            from sqlalchemy import select

            query = select(MemoryRecord).where(MemoryRecord.namespace == namespace)
            if scope:
                query = query.where(MemoryRecord.scope == scope.value)
            query = query.order_by(MemoryRecord.created_at.desc()).limit(limit)

            result = await session.execute(query)
            records = result.scalars().all()

            return [
                MemoryEntry(
                    id=r.id,
                    scope=MemoryScope(r.scope),
                    namespace=r.namespace,
                    content=r.content,
                    metadata=r.entry_metadata or {},
                )
                for r in records
            ]

    # Task methods
    async def save_task(self, task_data: Dict[str, Any]):
        """Save or update a task"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            from sqlalchemy import select
            from sqlalchemy.dialects.postgresql import insert
            
            # Check if task exists
            existing = await session.execute(
                select(TaskRecord).where(TaskRecord.id == task_data["id"])
            )
            record = existing.scalar_one_or_none()
            
            if record:
                # Update existing
                for key, value in task_data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = datetime.utcnow()
            else:
                # Create new
                record = TaskRecord(**task_data)
                session.add(record)
            
            await session.commit()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(TaskRecord).where(TaskRecord.id == task_id)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return None
            
            return {
                "id": record.id,
                "description": record.description,
                "status": record.status,
                "provider": record.provider,
                "context": record.context,
                "result": record.result,
                "error": record.error,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "completed_at": record.completed_at,
                "tokens_used": record.tokens_used,
                "agents_count": record.agents_count,
                "progress": record.progress,
                "debate_state": record.debate_state,
                "subtasks": record.subtasks,
                "validation_results": record.validation_results,
            }

    async def list_tasks(self, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            from sqlalchemy import select
            
            query = select(TaskRecord)
            if status:
                query = query.where(TaskRecord.status == status)
            query = query.order_by(TaskRecord.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            return [
                {
                    "id": r.id,
                    "description": r.description,
                    "status": r.status,
                    "provider": r.provider,
                    "created_at": r.created_at,
                    "agents_count": r.agents_count,
                    "tokens_used": r.tokens_used,
                    "progress": r.progress,
                }
                for r in records
            ]

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if not self.session_factory:
            await self.connect()
        async with self.session_factory() as session:
            from sqlalchemy import delete
            
            result = await session.execute(
                delete(TaskRecord).where(TaskRecord.id == task_id)
            )
            await session.commit()
            return result.rowcount > 0

