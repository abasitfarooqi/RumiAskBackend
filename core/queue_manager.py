"""
Queue Manager for Ask Rumi Backend
Handles async task queuing and concurrent request management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class QueueTask(BaseModel):
    """Queue task model"""
    id: str
    name: str
    function: str  # Function name to call
    args: Dict[str, Any] = {}
    kwargs: Dict[str, Any] = {}
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None  # seconds

class QueueManager:
    """Manages async task queue and concurrent execution"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, QueueTask] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.worker_tasks: List[asyncio.Task] = []
        self.registered_functions: Dict[str, Callable] = {}
        self.is_running = False
        
        # Priority weights (lower number = higher priority)
        self.priority_weights = {
            TaskPriority.URGENT: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.NORMAL: 3,
            TaskPriority.LOW: 4
        }
    
    def register_function(self, name: str, func: Callable):
        """Register a function that can be called by the queue"""
        self.registered_functions[name] = func
        logger.info(f"Registered function: {name}")
    
    async def start(self):
        """Start the queue manager"""
        if self.is_running:
            logger.warning("Queue manager is already running")
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        logger.info(f"Queue manager started with {self.max_concurrent_tasks} workers")
    
    async def stop(self):
        """Stop the queue manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all worker tasks
        for worker in self.worker_tasks:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
        
        logger.info("Queue manager stopped")
    
    async def enqueue_task(
        self,
        name: str,
        function: str,
        args: Dict[str, Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[int] = None,
        max_retries: int = 3
    ) -> str:
        """Enqueue a new task"""
        if not self.is_running:
            await self.start()
        
        task_id = str(uuid.uuid4())
        
        task = QueueTask(
            id=task_id,
            name=name,
            function=function,
            args=args or {},
            kwargs=kwargs or {},
            priority=priority,
            created_at=datetime.now(),
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        
        # Add to priority queue
        priority_weight = self.priority_weights[priority]
        await self.task_queue.put((priority_weight, task_id))
        
        logger.info(f"Enqueued task {task_id}: {name}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status by ID"""
        return self.tasks.get(task_id)
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result by ID"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"Cancelled pending task {task_id}")
            return True
        
        elif task.status == TaskStatus.RUNNING:
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                logger.info(f"Cancelled running task {task_id}")
                return True
        
        return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "total_tasks": len(self.tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]),
            "queue_size": self.task_queue.qsize(),
            "max_concurrent": self.max_concurrent_tasks,
            "is_running": self.is_running
        }
        return stats
    
    async def get_recent_tasks(self, limit: int = 10) -> List[QueueTask]:
        """Get recent tasks"""
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return sorted_tasks[:limit]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                and task.created_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes tasks"""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next task from queue
                priority_weight, task_id = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    continue
                
                # Execute task
                await self._execute_task(task, worker_name)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_task(self, task: QueueTask, worker_name: str):
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"Worker {worker_name} executing task {task.id}: {task.name}")
        
        try:
            # Get the function to execute
            func = self.registered_functions.get(task.function)
            if not func:
                raise ValueError(f"Function {task.function} not registered")
            
            # Execute with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    func(**task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await func(**task.args, **task.kwargs)
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            logger.info(f"Task {task.id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = f"Task timed out after {task.timeout} seconds"
            task.completed_at = datetime.now()
            logger.error(f"Task {task.id} timed out")
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                # Retry the task
                task.status = TaskStatus.PENDING
                priority_weight = self.priority_weights[task.priority]
                await self.task_queue.put((priority_weight, task.id))
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count + 1})")
            else:
                # Max retries exceeded
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(f"Task {task.id} failed after {task.max_retries} retries: {e}")
        
        finally:
            # Remove from running tasks
            self.running_tasks.pop(task.id, None)

# Global instance
queue_manager = QueueManager()

def get_queue_manager() -> QueueManager:
    """Get the global queue manager instance"""
    return queue_manager