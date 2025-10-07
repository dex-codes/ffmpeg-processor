"""
Cloud Run FastAPI application for video processing service.

This application provides REST API endpoints for processing videos stored in Google Cloud Storage.
Optimized for Cloud Run deployment with proper error handling, logging, and monitoring.

Endpoints:
- GET /health - Health check
- GET /videos/list - List available raw videos
- POST /videos/process - Process single video
- POST /videos/batch - Process multiple videos
- POST /videos/sequence - Process video sequence
- GET /presets - List available processing presets
- GET /stats - Get processing statistics

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from cloud_storage import create_storage_manager, CloudStorageManager
from video_processing_service import VideoProcessingService
from job_manager import JobManager, JobType
from config import init_config, get_config
from monitoring import structured_logger, performance_monitor, health_checker

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
storage_manager: Optional[CloudStorageManager] = None
video_service: Optional[VideoProcessingService] = None
job_manager: Optional[JobManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    global storage_manager, video_service, job_manager

    # Startup
    logger.info("Starting video processing service...")

    try:
        # Initialize configuration
        config = init_config()
        structured_logger.info("Configuration initialized", environment=config.environment)

        # Initialize Cloud Storage
        storage_manager = create_storage_manager(
            bucket_name=config.storage.bucket_name,
            project_id=config.storage.project_id
        )

        # Initialize services
        video_service = VideoProcessingService(storage_manager)
        job_manager = JobManager(max_concurrent_jobs=config.processing.max_concurrent_jobs)

        # Start monitoring
        performance_monitor.start_monitoring()

        # Register health checks
        health_checker.register_check("storage", lambda: storage_manager.check_connection())
        health_checker.register_check("ffmpeg", lambda: video_service._check_ffmpeg())

        structured_logger.info("Video processing service started successfully")

    except Exception as e:
        structured_logger.error(f"Failed to start service: {e}")
        raise

    yield

    # Shutdown
    structured_logger.info("Shutting down video processing service...")

    # Stop monitoring
    performance_monitor.stop_monitoring()

    # Cleanup any remaining temp files
    if video_service:
        try:
            await video_service.cleanup_old_files(max_age_hours=1)
        except Exception as e:
            structured_logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Video Processing Service",
    description="Cloud-native video processing service for Google Cloud Run",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class VideoProcessRequest(BaseModel):
    video_filename: str = Field(..., description="Name of video file in raw-video-clips folder")
    preset: str = Field(default="mobile_vertical", description="Video processing preset")
    custom_settings: Optional[Dict[str, Any]] = Field(default=None, description="Custom processing settings")


class BatchProcessRequest(BaseModel):
    video_filenames: List[str] = Field(..., description="List of video filenames to process")
    preset: str = Field(default="mobile_vertical", description="Video processing preset")
    max_concurrent: int = Field(default=2, description="Maximum concurrent processing jobs")


class SequenceProcessRequest(BaseModel):
    video_filenames: List[str] = Field(..., description="List of video filenames in desired order")
    output_filename: str = Field(..., description="Name for the final concatenated video")
    preset: str = Field(default="mobile_vertical", description="Video processing preset")
    custom_settings: Optional[Dict[str, Any]] = Field(default=None, description="Custom processing settings")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Video Processing Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Cloud-native video processing for Google Cloud Run"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health = await video_service.health_check()
    
    if health['status'] == 'unhealthy':
        raise HTTPException(status_code=503, detail="Service unhealthy", headers={"X-Health-Details": str(health)})
    
    return health


@app.get("/videos/list")
async def list_videos(
    prefix: str = Query(default="", description="Optional prefix to filter videos"),
    limit: int = Query(default=100, description="Maximum number of videos to return")
):
    """List available raw videos in GCS bucket."""
    if storage_manager is None:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    try:
        videos = storage_manager.list_raw_videos(prefix=prefix, limit=limit)
        return {
            "videos": videos,
            "count": len(videos),
            "prefix": prefix
        }
    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


@app.post("/videos/process")
async def process_video(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    """Process a single video."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    try:
        # For Cloud Run, we'll process synchronously for now
        # In production, you might want to use Cloud Tasks for async processing
        result = await video_service.process_single_video(
            video_filename=request.video_filename,
            preset=request.preset,
            custom_settings=request.custom_settings
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process video: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/videos/batch")
async def process_batch(request: BatchProcessRequest):
    """Process multiple videos concurrently."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    if len(request.video_filenames) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 videos per batch")
    
    try:
        result = await video_service.process_video_batch(
            video_filenames=request.video_filenames,
            preset=request.preset,
            max_concurrent=min(request.max_concurrent, 3)  # Limit for Cloud Run
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@app.post("/videos/sequence")
async def process_sequence(request: SequenceProcessRequest):
    """Process and concatenate multiple videos into a single output."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    if len(request.video_filenames) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 videos per sequence")
    
    try:
        result = await video_service.process_video_sequence(
            video_filenames=request.video_filenames,
            output_filename=request.output_filename,
            preset=request.preset,
            custom_settings=request.custom_settings
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process sequence: {e}")
        raise HTTPException(status_code=500, detail=f"Sequence processing failed: {str(e)}")


@app.get("/presets")
async def get_presets():
    """Get available video processing presets."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    return video_service.get_available_presets()


@app.get("/stats")
async def get_stats():
    """Get processing statistics."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    stats = video_service.get_processing_stats()
    
    # Add storage stats
    if storage_manager:
        storage_stats = storage_manager.get_storage_stats()
        stats['storage'] = storage_stats
    
    return stats


@app.post("/cleanup")
async def cleanup_files(max_age_hours: int = Query(default=24, description="Maximum age of files to keep")):
    """Clean up old temporary files."""
    if video_service is None:
        raise HTTPException(status_code=503, detail="Video service not initialized")
    
    try:
        cleanup_result = await video_service.cleanup_old_files(max_age_hours=max_age_hours)
        return cleanup_result
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
