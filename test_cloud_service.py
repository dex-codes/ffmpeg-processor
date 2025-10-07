"""
Comprehensive test suite for the Cloud Run video processing service.

This test suite covers all major components of the service including:
- Cloud Storage integration
- Video processing service
- FastAPI endpoints
- Job management
- Configuration management

Author: Cloud Migration
Date: 2025-01-07
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["GCS_BUCKET_NAME"] = "test-bucket"

from fastapi.testclient import TestClient
import httpx

# Import modules to test
from cloud_storage import CloudStorageManager
from video_processing_service import VideoProcessingService
from job_manager import JobManager, JobType, JobStatus
from config import Config, init_config
from main import app


class TestCloudStorageManager:
    """Test cases for CloudStorageManager."""
    
    @pytest.fixture
    def mock_storage_client(self):
        """Mock Google Cloud Storage client."""
        with patch('cloud_storage.storage') as mock_storage:
            mock_client = Mock()
            mock_bucket = Mock()
            mock_storage.Client.return_value = mock_client
            mock_client.bucket.return_value = mock_bucket
            yield mock_storage, mock_client, mock_bucket
    
    def test_init(self, mock_storage_client):
        """Test CloudStorageManager initialization."""
        mock_storage, mock_client, mock_bucket = mock_storage_client
        
        manager = CloudStorageManager(bucket_name="test-bucket")
        
        assert manager.bucket_name == "test-bucket"
        assert manager.raw_folder == "raw-video-clips"
        assert manager.processed_folder == "processed-video-clips"
        assert manager.temp_folder == "temp-service-folder"
    
    def test_check_connection(self, mock_storage_client):
        """Test connection check."""
        mock_storage, mock_client, mock_bucket = mock_storage_client
        
        manager = CloudStorageManager(bucket_name="test-bucket")
        
        # Test successful connection
        mock_bucket.reload.return_value = None
        assert manager.check_connection() == True
        
        # Test failed connection
        mock_bucket.reload.side_effect = Exception("Connection failed")
        assert manager.check_connection() == False
    
    def test_list_raw_videos(self, mock_storage_client):
        """Test listing raw videos."""
        mock_storage, mock_client, mock_bucket = mock_storage_client
        
        manager = CloudStorageManager(bucket_name="test-bucket")
        
        # Mock blob objects
        mock_blob1 = Mock()
        mock_blob1.name = "raw-video-clips/video1.mp4"
        mock_blob1.size = 1000000
        mock_blob1.time_created = datetime.now()
        mock_blob1.updated = datetime.now()
        mock_blob1.content_type = "video/mp4"
        mock_blob1.md5_hash = "abc123"
        
        mock_blob2 = Mock()
        mock_blob2.name = "raw-video-clips/video2.mp4"
        mock_blob2.size = 2000000
        mock_blob2.time_created = datetime.now()
        mock_blob2.updated = datetime.now()
        mock_blob2.content_type = "video/mp4"
        mock_blob2.md5_hash = "def456"
        
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        videos = manager.list_raw_videos()
        
        assert len(videos) == 2
        assert videos[0]['filename'] == 'video1.mp4'
        assert videos[1]['filename'] == 'video2.mp4'
    
    @pytest.mark.asyncio
    async def test_download_raw_video(self, mock_storage_client):
        """Test downloading raw video."""
        mock_storage, mock_client, mock_bucket = mock_storage_client
        
        manager = CloudStorageManager(bucket_name="test-bucket")
        
        # Mock blob
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        
        # Create temporary file to simulate download
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake video data")
        
        # Mock download
        def mock_download(filename):
            with open(filename, 'wb') as f:
                f.write(b"fake video data")
        
        mock_blob.download_to_filename = mock_download
        
        result = await manager.download_raw_video("test.mp4", temp_path)
        
        assert result == temp_path
        assert temp_path.exists()
        
        # Cleanup
        temp_path.unlink()


class TestVideoProcessingService:
    """Test cases for VideoProcessingService."""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """Mock storage manager."""
        return Mock(spec=CloudStorageManager)
    
    @pytest.fixture
    def video_service(self, mock_storage_manager):
        """Create video processing service with mocked storage."""
        return VideoProcessingService(mock_storage_manager)
    
    def test_init(self, video_service):
        """Test service initialization."""
        assert video_service.storage is not None
        assert video_service.processing_stats['jobs_processed'] == 0
        assert video_service.work_dir.exists()
    
    def test_generate_job_id(self, video_service):
        """Test job ID generation."""
        job_id = video_service._generate_job_id()
        
        assert job_id.startswith("job_")
        assert len(job_id) > 20  # Should include timestamp and random part
    
    @patch('video_processing_service.subprocess.run')
    def test_check_ffmpeg(self, mock_subprocess, video_service):
        """Test FFmpeg availability check."""
        # Test FFmpeg available
        mock_subprocess.return_value = Mock(returncode=0)
        assert video_service._check_ffmpeg() == True
        
        # Test FFmpeg not available
        mock_subprocess.side_effect = FileNotFoundError()
        assert video_service._check_ffmpeg() == False
    
    @pytest.mark.asyncio
    async def test_health_check(self, video_service):
        """Test health check."""
        with patch.object(video_service, '_check_ffmpeg', return_value=True):
            video_service.storage.check_connection.return_value = True
            
            health = await video_service.health_check()
            
            assert health['status'] == 'healthy'
            assert health['ffmpeg_available'] == True
            assert health['gcs_connection'] == True


class TestJobManager:
    """Test cases for JobManager."""
    
    @pytest.fixture
    def job_manager(self):
        """Create job manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield JobManager(max_concurrent_jobs=2, persistence_dir=Path(temp_dir))
    
    def test_init(self, job_manager):
        """Test job manager initialization."""
        assert job_manager.max_concurrent_jobs == 2
        assert len(job_manager.jobs) == 0
        assert job_manager.persistence_dir.exists()
    
    def test_create_job(self, job_manager):
        """Test job creation."""
        job_id = job_manager.create_job(
            job_type=JobType.SINGLE_VIDEO,
            parameters={"video_filename": "test.mp4"},
            metadata={"user": "test"}
        )
        
        assert job_id in job_manager.jobs
        job_info = job_manager.jobs[job_id]
        assert job_info.job_type == JobType.SINGLE_VIDEO
        assert job_info.status == JobStatus.PENDING
        assert job_info.parameters["video_filename"] == "test.mp4"
    
    def test_get_job(self, job_manager):
        """Test getting job information."""
        job_id = job_manager.create_job(
            job_type=JobType.BATCH_PROCESS,
            parameters={"videos": ["v1.mp4", "v2.mp4"]}
        )
        
        job_info = job_manager.get_job(job_id)
        assert job_info is not None
        assert job_info.job_id == job_id
        
        # Test non-existent job
        assert job_manager.get_job("non-existent") is None
    
    def test_list_jobs(self, job_manager):
        """Test listing jobs with filters."""
        # Create test jobs
        job1 = job_manager.create_job(JobType.SINGLE_VIDEO, {"video": "v1.mp4"})
        job2 = job_manager.create_job(JobType.BATCH_PROCESS, {"videos": ["v2.mp4"]})
        
        # Test list all jobs
        all_jobs = job_manager.list_jobs()
        assert len(all_jobs) == 2
        
        # Test filter by job type
        single_jobs = job_manager.list_jobs(job_type=JobType.SINGLE_VIDEO)
        assert len(single_jobs) == 1
        assert single_jobs[0].job_id == job1
        
        # Test filter by status
        pending_jobs = job_manager.list_jobs(status=JobStatus.PENDING)
        assert len(pending_jobs) == 2
    
    @pytest.mark.asyncio
    async def test_execute_job(self, job_manager):
        """Test job execution."""
        # Create a test job
        job_id = job_manager.create_job(
            job_type=JobType.SINGLE_VIDEO,
            parameters={"test": "data"}
        )
        
        # Mock job function
        async def mock_job_function(params):
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": "success", "params": params}
        
        # Execute job
        await job_manager.execute_job(job_id, mock_job_function)
        
        # Check job status
        job_info = job_manager.get_job(job_id)
        assert job_info.status == JobStatus.COMPLETED
        assert job_info.result["result"] == "success"
        assert job_info.started_at is not None
        assert job_info.completed_at is not None


class TestConfig:
    """Test cases for configuration management."""
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        config = Config(environment="test")
        
        assert config.environment == "test"
        assert config.storage.bucket_name == "bg-video-storage"
        assert config.processing.max_concurrent_jobs >= 1
        assert config.server.port == 8080
    
    def test_environment_specific_config(self):
        """Test environment-specific configuration."""
        # Test development environment
        dev_config = Config(environment="development")
        assert dev_config.processing.max_concurrent_jobs == 2
        
        # Test production environment
        prod_config = Config(environment="production")
        assert prod_config.processing.max_concurrent_jobs == 5
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid configuration
        with patch.dict(os.environ, {"MAX_CONCURRENT_JOBS": "0"}):
            with pytest.raises(ValueError):
                Config(environment="test")


class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Video Processing Service"
        assert data["status"] == "running"
    
    @patch('main.video_service')
    def test_health_endpoint(self, mock_service, client):
        """Test health endpoint."""
        # Mock healthy service
        mock_service.health_check.return_value = {
            "status": "healthy",
            "ffmpeg_available": True,
            "gcs_connection": True
        }
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('main.storage_manager')
    def test_list_videos_endpoint(self, mock_storage, client):
        """Test list videos endpoint."""
        # Mock video list
        mock_storage.list_raw_videos.return_value = [
            {"filename": "video1.mp4", "size": 1000000},
            {"filename": "video2.mp4", "size": 2000000}
        ]
        
        response = client.get("/videos/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data["videos"]) == 2
        assert data["count"] == 2
    
    @patch('main.video_service')
    def test_process_video_endpoint(self, mock_service, client):
        """Test process video endpoint."""
        # Mock processing result
        mock_service.process_single_video.return_value = {
            "job_id": "test_job_123",
            "status": "completed",
            "video_filename": "test.mp4"
        }
        
        request_data = {
            "video_filename": "test.mp4",
            "preset": "mobile_vertical"
        }
        
        response = client.post("/videos/process", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test_job_123"
        assert data["status"] == "completed"
    
    def test_get_presets_endpoint(self, client):
        """Test get presets endpoint."""
        with patch('main.video_service') as mock_service:
            mock_service.get_available_presets.return_value = {
                "presets": {"mobile_vertical": {"frame_width": 1080}}
            }
            
            response = client.get("/presets")
            assert response.status_code == 200
            data = response.json()
            assert "presets" in data


class TestIntegration:
    """Integration tests for the complete service."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from video upload to processing."""
        # This would be a more complex test that simulates:
        # 1. Uploading a video to GCS
        # 2. Processing it through the service
        # 3. Verifying the output
        
        # For now, we'll test the workflow with mocks
        with patch('cloud_storage.storage'):
            storage_manager = CloudStorageManager("test-bucket")
            video_service = VideoProcessingService(storage_manager)
            
            # Mock the storage operations
            storage_manager.download_raw_video = AsyncMock(return_value=Path("/tmp/test.mp4"))
            storage_manager.upload_processed_video = AsyncMock(return_value="gs://test/output.mp4")
            
            # Mock FFmpeg processing
            with patch('video_processing_service.convert_video_format') as mock_convert:
                mock_convert.return_value = "/tmp/processed.mp4"
                
                # Create a fake processed file
                processed_file = Path("/tmp/processed.mp4")
                processed_file.touch()
                
                try:
                    # Test the workflow
                    result = await video_service.process_single_video(
                        video_filename="test.mp4",
                        preset="mobile_vertical"
                    )
                    
                    assert result["status"] == "completed"
                    assert "job_id" in result
                    
                finally:
                    # Cleanup
                    if processed_file.exists():
                        processed_file.unlink()


# Test fixtures and utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
