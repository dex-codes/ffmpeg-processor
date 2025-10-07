"""
Environment configuration for video processing service.

This module handles configuration management for different deployment environments
including development, staging, and production.

Features:
- Environment-specific settings
- Secret management integration
- Configuration validation
- Default values and overrides

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Google Cloud Storage configuration."""
    bucket_name: str = "bg-video-storage"
    project_id: Optional[str] = None
    raw_folder: str = "raw-video-clips"
    processed_folder: str = "processed-video-clips"
    temp_folder: str = "temp-service-folder"
    
    # Cleanup settings
    temp_file_max_age_hours: int = 24
    job_max_age_days: int = 7


@dataclass
class ProcessingConfig:
    """Video processing configuration."""
    max_concurrent_jobs: int = 3
    max_concurrent_downloads: int = 3
    max_workers_per_job: int = 2
    default_preset: str = "mobile_vertical"
    
    # Limits
    max_batch_size: int = 10
    max_sequence_size: int = 20
    max_file_size_mb: int = 500
    
    # Timeouts
    processing_timeout_seconds: int = 3600  # 1 hour
    download_timeout_seconds: int = 300     # 5 minutes
    upload_timeout_seconds: int = 600       # 10 minutes


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    log_level: str = "INFO"
    
    # CORS settings
    cors_origins: list = None
    cors_allow_credentials: bool = True
    cors_allow_methods: list = None
    cors_allow_headers: list = None
    
    # Health check settings
    health_check_interval: int = 30
    startup_timeout: int = 300


@dataclass
class CloudRunConfig:
    """Cloud Run specific configuration."""
    memory: str = "4Gi"
    cpu: str = "2"
    timeout: int = 3600
    concurrency: int = 10
    max_instances: int = 5
    min_instances: int = 0
    
    # Service account
    service_account: Optional[str] = None
    
    # VPC settings
    vpc_connector: Optional[str] = None
    vpc_egress: str = "private-ranges-only"


class Config:
    """Main configuration class that loads settings from environment variables."""
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            environment: Deployment environment (development, staging, production)
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        
        # Load configurations
        self.storage = self._load_storage_config()
        self.processing = self._load_processing_config()
        self.server = self._load_server_config()
        self.cloud_run = self._load_cloud_run_config()
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Configuration loaded for environment: {self.environment}")
    
    def _load_storage_config(self) -> StorageConfig:
        """Load storage configuration from environment variables."""
        return StorageConfig(
            bucket_name=os.getenv("GCS_BUCKET_NAME", "bg-video-storage"),
            project_id=os.getenv("GCP_PROJECT_ID"),
            raw_folder=os.getenv("GCS_RAW_FOLDER", "raw-video-clips"),
            processed_folder=os.getenv("GCS_PROCESSED_FOLDER", "processed-video-clips"),
            temp_folder=os.getenv("GCS_TEMP_FOLDER", "temp-service-folder"),
            temp_file_max_age_hours=int(os.getenv("TEMP_FILE_MAX_AGE_HOURS", "24")),
            job_max_age_days=int(os.getenv("JOB_MAX_AGE_DAYS", "7"))
        )
    
    def _load_processing_config(self) -> ProcessingConfig:
        """Load processing configuration from environment variables."""
        # Adjust defaults based on environment
        if self.environment == "production":
            max_concurrent = 5
            max_workers = 4
        elif self.environment == "staging":
            max_concurrent = 3
            max_workers = 2
        else:  # development
            max_concurrent = 2
            max_workers = 1
        
        return ProcessingConfig(
            max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", str(max_concurrent))),
            max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3")),
            max_workers_per_job=int(os.getenv("MAX_WORKERS_PER_JOB", str(max_workers))),
            default_preset=os.getenv("DEFAULT_PRESET", "mobile_vertical"),
            max_batch_size=int(os.getenv("MAX_BATCH_SIZE", "10")),
            max_sequence_size=int(os.getenv("MAX_SEQUENCE_SIZE", "20")),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "500")),
            processing_timeout_seconds=int(os.getenv("PROCESSING_TIMEOUT", "3600")),
            download_timeout_seconds=int(os.getenv("DOWNLOAD_TIMEOUT", "300")),
            upload_timeout_seconds=int(os.getenv("UPLOAD_TIMEOUT", "600"))
        )
    
    def _load_server_config(self) -> ServerConfig:
        """Load server configuration from environment variables."""
        # Parse CORS origins
        cors_origins = os.getenv("CORS_ORIGINS")
        if cors_origins:
            cors_origins = [origin.strip() for origin in cors_origins.split(",")]
        else:
            cors_origins = ["*"] if self.environment == "development" else []
        
        # Parse CORS methods and headers
        cors_methods = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
        cors_headers = os.getenv("CORS_HEADERS", "*").split(",")
        
        return ServerConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cors_origins=cors_origins,
            cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            cors_allow_methods=cors_methods,
            cors_allow_headers=cors_headers,
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            startup_timeout=int(os.getenv("STARTUP_TIMEOUT", "300"))
        )
    
    def _load_cloud_run_config(self) -> CloudRunConfig:
        """Load Cloud Run specific configuration."""
        return CloudRunConfig(
            memory=os.getenv("CLOUD_RUN_MEMORY", "4Gi"),
            cpu=os.getenv("CLOUD_RUN_CPU", "2"),
            timeout=int(os.getenv("CLOUD_RUN_TIMEOUT", "3600")),
            concurrency=int(os.getenv("CLOUD_RUN_CONCURRENCY", "10")),
            max_instances=int(os.getenv("CLOUD_RUN_MAX_INSTANCES", "5")),
            min_instances=int(os.getenv("CLOUD_RUN_MIN_INSTANCES", "0")),
            service_account=os.getenv("CLOUD_RUN_SERVICE_ACCOUNT"),
            vpc_connector=os.getenv("CLOUD_RUN_VPC_CONNECTOR"),
            vpc_egress=os.getenv("CLOUD_RUN_VPC_EGRESS", "private-ranges-only")
        )
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        errors = []
        
        # Validate storage config
        if not self.storage.bucket_name:
            errors.append("GCS bucket name is required")
        
        # Validate processing limits
        if self.processing.max_concurrent_jobs < 1:
            errors.append("Max concurrent jobs must be at least 1")
        
        if self.processing.max_batch_size < 1:
            errors.append("Max batch size must be at least 1")
        
        # Validate server config
        if not (1 <= self.server.port <= 65535):
            errors.append("Server port must be between 1 and 65535")
        
        # Validate Cloud Run config
        if self.cloud_run.concurrency < 1:
            errors.append("Cloud Run concurrency must be at least 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging."""
        return {
            "environment": self.environment,
            "storage": {
                "bucket_name": self.storage.bucket_name,
                "project_id": self.storage.project_id,
                "folders": {
                    "raw": self.storage.raw_folder,
                    "processed": self.storage.processed_folder,
                    "temp": self.storage.temp_folder
                }
            },
            "processing": {
                "max_concurrent_jobs": self.processing.max_concurrent_jobs,
                "max_workers_per_job": self.processing.max_workers_per_job,
                "default_preset": self.processing.default_preset
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
                "log_level": self.server.log_level
            }
        }
    
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.server.log_level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
        
        # Set specific logger levels
        if self.environment == "production":
            # Reduce noise in production
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
            logging.getLogger("google.auth").setLevel(logging.WARNING)
        
        logger.info(f"Logging configured for {self.environment} environment")


# Global configuration instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = Config()
    return config


def init_config(environment: Optional[str] = None) -> Config:
    """Initialize the global configuration."""
    global config
    config = Config(environment=environment)
    config.setup_logging()
    return config
