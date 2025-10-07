"""
Async job processing system for video processing service.

This module provides background job processing capabilities for long-running video operations
with proper status tracking, error handling, and job persistence.

Features:
- Async job execution with status tracking
- Job persistence and recovery
- Progress monitoring
- Error handling and retry logic
- Job queuing and concurrency control

Author: Cloud Migration
Date: 2025-01-07
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    """Job type enumeration."""
    SINGLE_VIDEO = "single_video"
    BATCH_PROCESS = "batch_process"
    VIDEO_SEQUENCE = "video_sequence"
    CLEANUP = "cleanup"


@dataclass
class JobInfo:
    """Job information data class."""
    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key] is not None:
                data[key] = data[key].isoformat()
        # Convert enums to strings
        data['status'] = self.status.value
        data['job_type'] = self.job_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobInfo':
        """Create JobInfo from dictionary."""
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'started_at', 'completed_at']:
            if data.get(key) is not None:
                data[key] = datetime.fromisoformat(data[key])
        # Convert strings back to enums
        data['status'] = JobStatus(data['status'])
        data['job_type'] = JobType(data['job_type'])
        return cls(**data)


class JobManager:
    """
    Manages background job processing with status tracking and persistence.
    """
    
    def __init__(self, max_concurrent_jobs: int = 3, persistence_dir: Optional[Path] = None):
        """
        Initialize job manager.
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent jobs
            persistence_dir: Directory for job persistence (None for temp dir)
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: Dict[str, JobInfo] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.job_semaphore = asyncio.Semaphore(max_concurrent_jobs)
        
        # Setup persistence
        if persistence_dir is None:
            persistence_dir = Path(tempfile.gettempdir()) / "video_jobs"
        self.persistence_dir = persistence_dir
        self.persistence_dir.mkdir(exist_ok=True)
        
        # Load existing jobs
        self._load_jobs()
        
        logger.info(f"JobManager initialized with max {max_concurrent_jobs} concurrent jobs")
    
    def _get_job_file(self, job_id: str) -> Path:
        """Get file path for job persistence."""
        return self.persistence_dir / f"{job_id}.json"
    
    def _save_job(self, job_info: JobInfo) -> None:
        """Save job to persistent storage."""
        try:
            job_file = self._get_job_file(job_info.job_id)
            with open(job_file, 'w') as f:
                json.dump(job_info.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save job {job_info.job_id}: {e}")
    
    def _load_jobs(self) -> None:
        """Load jobs from persistent storage."""
        try:
            for job_file in self.persistence_dir.glob("*.json"):
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                    job_info = JobInfo.from_dict(job_data)
                    self.jobs[job_info.job_id] = job_info
                    
                    # Reset running jobs to pending on startup
                    if job_info.status == JobStatus.RUNNING:
                        job_info.status = JobStatus.PENDING
                        self._save_job(job_info)
                        
                except Exception as e:
                    logger.error(f"Failed to load job from {job_file}: {e}")
                    
            logger.info(f"Loaded {len(self.jobs)} jobs from persistence")
            
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
    
    def create_job(self, 
                   job_type: JobType,
                   parameters: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new job.
        
        Args:
            job_type: Type of job to create
            parameters: Job parameters
            metadata: Optional job metadata
            
        Returns:
            Job ID
        """
        job_id = f"{job_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        job_info = JobInfo(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            parameters=parameters,
            metadata=metadata or {}
        )
        
        self.jobs[job_id] = job_info
        self._save_job(job_info)
        
        logger.info(f"Created job {job_id} of type {job_type.value}")
        return job_id
    
    async def execute_job(self, 
                         job_id: str, 
                         job_function: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
                         progress_callback: Optional[Callable[[str, float], None]] = None) -> None:
        """
        Execute a job with the given function.
        
        Args:
            job_id: Job ID to execute
            job_function: Async function to execute the job
            progress_callback: Optional callback for progress updates
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job_info = self.jobs[job_id]
        
        if job_info.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in pending status")
        
        async with self.job_semaphore:
            try:
                # Update job status to running
                job_info.status = JobStatus.RUNNING
                job_info.started_at = datetime.now()
                self._save_job(job_info)
                
                logger.info(f"Starting execution of job {job_id}")
                
                # Execute the job function
                result = await job_function(job_info.parameters)
                
                # Update job with result
                job_info.status = JobStatus.COMPLETED
                job_info.completed_at = datetime.now()
                job_info.progress = 100.0
                job_info.result = result
                self._save_job(job_info)
                
                logger.info(f"Job {job_id} completed successfully")
                
            except asyncio.CancelledError:
                job_info.status = JobStatus.CANCELLED
                job_info.completed_at = datetime.now()
                job_info.error = "Job was cancelled"
                self._save_job(job_info)
                logger.info(f"Job {job_id} was cancelled")
                raise
                
            except Exception as e:
                job_info.status = JobStatus.FAILED
                job_info.completed_at = datetime.now()
                job_info.error = str(e)
                self._save_job(job_info)
                logger.error(f"Job {job_id} failed: {e}")
                raise
            
            finally:
                # Remove from running tasks
                if job_id in self.running_tasks:
                    del self.running_tasks[job_id]
    
    async def submit_job(self, 
                        job_type: JobType,
                        parameters: Dict[str, Any],
                        job_function: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a job for execution.
        
        Args:
            job_type: Type of job
            parameters: Job parameters
            job_function: Function to execute
            metadata: Optional metadata
            
        Returns:
            Job ID
        """
        job_id = self.create_job(job_type, parameters, metadata)
        
        # Create and start the task
        task = asyncio.create_task(self.execute_job(job_id, job_function))
        self.running_tasks[job_id] = task
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information by ID."""
        return self.jobs.get(job_id)
    
    def list_jobs(self, 
                  status: Optional[JobStatus] = None,
                  job_type: Optional[JobType] = None,
                  limit: Optional[int] = None) -> List[JobInfo]:
        """
        List jobs with optional filtering.
        
        Args:
            status: Filter by job status
            job_type: Filter by job type
            limit: Maximum number of jobs to return
            
        Returns:
            List of job information
        """
        jobs = list(self.jobs.values())
        
        # Apply filters
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        
        if job_type is not None:
            jobs = [job for job in jobs if job.job_type == job_type]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        if limit is not None:
            jobs = jobs[:limit]
        
        return jobs
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False if not found or not running
        """
        if job_id not in self.jobs:
            return False
        
        job_info = self.jobs[job_id]
        
        if job_info.status != JobStatus.RUNNING:
            return False
        
        # Cancel the task
        if job_id in self.running_tasks:
            task = self.running_tasks[job_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            return True
        
        return False
    
    def cleanup_old_jobs(self, max_age_days: int = 7) -> int:
        """
        Clean up old completed/failed jobs.
        
        Args:
            max_age_days: Maximum age of jobs to keep
            
        Returns:
            Number of jobs cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        jobs_to_remove = []
        
        for job_id, job_info in self.jobs.items():
            if (job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                job_info.created_at < cutoff_date):
                jobs_to_remove.append(job_id)
        
        # Remove jobs
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            
            # Remove persistence file
            try:
                job_file = self._get_job_file(job_id)
                if job_file.exists():
                    job_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove job file for {job_id}: {e}")
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        return len(jobs_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get job manager statistics."""
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = len([j for j in self.jobs.values() if j.status == status])
        
        return {
            'total_jobs': len(self.jobs),
            'running_jobs': len(self.running_tasks),
            'max_concurrent': self.max_concurrent_jobs,
            'status_counts': status_counts,
            'persistence_dir': str(self.persistence_dir)
        }
