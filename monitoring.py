"""
Monitoring and observability module for video processing service.

This module provides structured logging, metrics collection, and health monitoring
for the Cloud Run video processing service.

Features:
- Structured logging with Cloud Logging integration
- Performance metrics and timing
- Health check endpoints
- Error tracking and alerting
- Resource usage monitoring

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import time
import logging
import psutil
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import json

# Cloud Logging integration (optional)
try:
    from google.cloud import logging as cloud_logging
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data class."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    active_jobs: int
    total_jobs_processed: int
    average_processing_time: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class HealthStatus:
    """Health status data class."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    checks: Dict[str, bool]
    metrics: Optional[PerformanceMetrics] = None
    errors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.metrics:
            data['metrics'] = self.metrics.to_dict()
        return data


class StructuredLogger:
    """Structured logger with Cloud Logging integration."""
    
    def __init__(self, service_name: str = "video-processing-service"):
        """
        Initialize structured logger.
        
        Args:
            service_name: Name of the service for logging context
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        
        # Setup Cloud Logging if available and in Cloud Run
        if CLOUD_LOGGING_AVAILABLE and os.getenv("K_SERVICE"):
            try:
                client = cloud_logging.Client()
                client.setup_logging()
                self.logger.info("Cloud Logging configured")
            except Exception as e:
                self.logger.warning(f"Failed to setup Cloud Logging: {e}")
    
    def _create_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Create structured log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
            "severity": level.upper()
        }
        
        # Add Cloud Run specific fields
        if os.getenv("K_SERVICE"):
            entry.update({
                "service_name": os.getenv("K_SERVICE"),
                "service_version": os.getenv("K_REVISION"),
                "trace": kwargs.get("trace_id"),
                "span": kwargs.get("span_id")
            })
        
        # Add custom fields
        for key, value in kwargs.items():
            if key not in ["trace_id", "span_id"]:
                entry[key] = value
        
        return entry
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        entry = self._create_log_entry("info", message, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        entry = self._create_log_entry("warning", message, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        entry = self._create_log_entry("error", message, **kwargs)
        self.logger.error(json.dumps(entry))
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        entry = self._create_log_entry("debug", message, **kwargs)
        self.logger.debug(json.dumps(entry))


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, collection_interval: int = 60):
        """
        Initialize performance monitor.
        
        Args:
            collection_interval: Metrics collection interval in seconds
        """
        self.collection_interval = collection_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1440  # 24 hours at 1-minute intervals
        self.job_stats = {
            'total_processed': 0,
            'total_errors': 0,
            'processing_times': [],
            'active_jobs': 0
        }
        self.logger = StructuredLogger("performance-monitor")
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def start_monitoring(self):
        """Start background monitoring task."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate average processing time
        avg_processing_time = 0.0
        if self.job_stats['processing_times']:
            avg_processing_time = sum(self.job_stats['processing_times']) / len(self.job_stats['processing_times'])
        
        # Calculate error rate
        error_rate = 0.0
        total_jobs = self.job_stats['total_processed'] + self.job_stats['total_errors']
        if total_jobs > 0:
            error_rate = self.job_stats['total_errors'] / total_jobs
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            disk_usage_percent=disk.percent,
            active_jobs=self.job_stats['active_jobs'],
            total_jobs_processed=self.job_stats['total_processed'],
            average_processing_time=avg_processing_time,
            error_rate=error_rate
        )
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """Store metrics in history."""
        self.metrics_history.append(metrics)
        
        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # Log metrics periodically
        if len(self.metrics_history) % 10 == 0:  # Every 10 minutes
            self.logger.info(
                "Performance metrics collected",
                cpu_percent=metrics.cpu_percent,
                memory_percent=metrics.memory_percent,
                active_jobs=metrics.active_jobs,
                error_rate=metrics.error_rate
            )
    
    def record_job_start(self):
        """Record job start."""
        self.job_stats['active_jobs'] += 1
    
    def record_job_completion(self, processing_time: float, success: bool = True):
        """Record job completion."""
        self.job_stats['active_jobs'] = max(0, self.job_stats['active_jobs'] - 1)
        
        if success:
            self.job_stats['total_processed'] += 1
            self.job_stats['processing_times'].append(processing_time)
            
            # Keep only recent processing times
            if len(self.job_stats['processing_times']) > 100:
                self.job_stats['processing_times'] = self.job_stats['processing_times'][-100:]
        else:
            self.job_stats['total_errors'] += 1
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self._collect_metrics()
    
    def get_metrics_history(self, hours: int = 1) -> List[PerformanceMetrics]:
        """Get metrics history for specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]


class HealthChecker:
    """Health check system for service monitoring."""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        """
        Initialize health checker.
        
        Args:
            performance_monitor: Performance monitor instance
        """
        self.performance_monitor = performance_monitor
        self.logger = StructuredLogger("health-checker")
        self.health_checks = {}
        self.thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 0.1,  # 10%
            'max_active_jobs': 10
        }
    
    def register_check(self, name: str, check_function: callable):
        """Register a health check function."""
        self.health_checks[name] = check_function
        self.logger.info(f"Registered health check: {name}")
    
    async def perform_health_check(self) -> HealthStatus:
        """Perform comprehensive health check."""
        checks = {}
        errors = []
        
        # System health checks
        try:
            metrics = self.performance_monitor.get_current_metrics()
            
            # CPU check
            checks['cpu'] = metrics.cpu_percent < self.thresholds['cpu_percent']
            if not checks['cpu']:
                errors.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
            # Memory check
            checks['memory'] = metrics.memory_percent < self.thresholds['memory_percent']
            if not checks['memory']:
                errors.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            
            # Disk check
            checks['disk'] = metrics.disk_usage_percent < self.thresholds['disk_usage_percent']
            if not checks['disk']:
                errors.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
            
            # Error rate check
            checks['error_rate'] = metrics.error_rate < self.thresholds['error_rate']
            if not checks['error_rate']:
                errors.append(f"High error rate: {metrics.error_rate:.2%}")
            
            # Active jobs check
            checks['active_jobs'] = metrics.active_jobs < self.thresholds['max_active_jobs']
            if not checks['active_jobs']:
                errors.append(f"Too many active jobs: {metrics.active_jobs}")
            
        except Exception as e:
            checks['system_metrics'] = False
            errors.append(f"Failed to collect system metrics: {e}")
            metrics = None
        
        # Custom health checks
        for name, check_function in self.health_checks.items():
            try:
                checks[name] = await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()
                if not checks[name]:
                    errors.append(f"Health check failed: {name}")
            except Exception as e:
                checks[name] = False
                errors.append(f"Health check error ({name}): {e}")
        
        # Determine overall status
        if not errors:
            status = "healthy"
        elif len(errors) <= 2:
            status = "degraded"
        else:
            status = "unhealthy"
        
        health_status = HealthStatus(
            status=status,
            timestamp=datetime.now(),
            checks=checks,
            metrics=metrics,
            errors=errors
        )
        
        # Log health status
        if status != "healthy":
            self.logger.warning(
                f"Health check status: {status}",
                errors=errors,
                failed_checks=[name for name, passed in checks.items() if not passed]
            )
        
        return health_status


@asynccontextmanager
async def performance_monitoring(monitor: PerformanceMonitor):
    """Context manager for performance monitoring."""
    start_time = time.time()
    monitor.record_job_start()
    
    try:
        yield
        # Job completed successfully
        processing_time = time.time() - start_time
        monitor.record_job_completion(processing_time, success=True)
    except Exception:
        # Job failed
        processing_time = time.time() - start_time
        monitor.record_job_completion(processing_time, success=False)
        raise


# Global instances
structured_logger = StructuredLogger()
performance_monitor = PerformanceMonitor()
health_checker = HealthChecker(performance_monitor)
