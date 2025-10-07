"""
Google Cloud Storage integration module for video processing service.

This module handles all interactions with Google Cloud Storage including:
- Downloading raw videos from bg-video-storage/raw-video-clips
- Uploading processed videos to bg-video-storage/processed-video-clips  
- Managing temporary files in bg-video-storage/temp-service-folder
- File operations with proper error handling and logging

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import aiofiles

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound, GoogleCloudError
    from google.api_core import retry
except ImportError:
    storage = None
    NotFound = Exception
    GoogleCloudError = Exception
    retry = None

logger = logging.getLogger(__name__)


class CloudStorageManager:
    """
    Manages Google Cloud Storage operations for video processing.
    
    Bucket structure:
    - bg-video-storage/raw-video-clips/        (source videos)
    - bg-video-storage/processed-video-clips/  (output videos)
    - bg-video-storage/temp-service-folder/    (temporary processing files)
    """
    
    def __init__(self, bucket_name: str = "bg-video-storage", 
                 project_id: Optional[str] = None):
        """
        Initialize Cloud Storage manager.
        
        Args:
            bucket_name: GCS bucket name (default: bg-video-storage)
            project_id: GCP project ID (auto-detected if None)
        """
        if storage is None:
            raise ImportError("google-cloud-storage is required. Install with: pip install google-cloud-storage")
        
        self.bucket_name = bucket_name
        self.project_id = project_id
        
        # Folder structure
        self.raw_folder = "raw-video-clips"
        self.processed_folder = "processed-video-clips"
        self.temp_folder = "temp-service-folder"
        
        # Initialize client and bucket
        self._client = None
        self._bucket = None
        
        # Local temp directory for processing
        self.local_temp_dir = Path(tempfile.gettempdir()) / "video_processing"
        self.local_temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"CloudStorageManager initialized for bucket: {bucket_name}")
    
    @property
    def client(self) -> storage.Client:
        """Lazy initialization of storage client."""
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client
    
    @property
    def bucket(self) -> storage.Bucket:
        """Lazy initialization of storage bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket
    
    def check_connection(self) -> bool:
        """
        Test connection to Google Cloud Storage.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to access bucket metadata
            self.bucket.reload()
            logger.info(f"Successfully connected to bucket: {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to bucket {self.bucket_name}: {e}")
            return False
    
    def list_raw_videos(self, prefix: str = "", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List available raw videos in the source folder.
        
        Args:
            prefix: Optional prefix to filter files
            limit: Maximum number of files to return
            
        Returns:
            List of video file metadata dictionaries
        """
        try:
            blob_prefix = f"{self.raw_folder}/{prefix}" if prefix else f"{self.raw_folder}/"
            blobs = self.bucket.list_blobs(prefix=blob_prefix, max_results=limit)
            
            videos = []
            for blob in blobs:
                # Skip directory markers and non-video files
                if blob.name.endswith('/') or not self._is_video_file(blob.name):
                    continue
                
                videos.append({
                    'name': blob.name,
                    'filename': Path(blob.name).name,
                    'size': blob.size,
                    'created': blob.time_created,
                    'updated': blob.updated,
                    'content_type': blob.content_type,
                    'md5_hash': blob.md5_hash
                })
            
            logger.info(f"Found {len(videos)} raw videos with prefix '{prefix}'")
            return videos
            
        except Exception as e:
            logger.error(f"Failed to list raw videos: {e}")
            return []
    
    async def download_raw_video(self, video_filename: str, 
                               local_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download a raw video file to local storage.
        
        Args:
            video_filename: Name of video file in raw-video-clips folder
            local_path: Optional local path (auto-generated if None)
            
        Returns:
            Path to downloaded file, None if failed
        """
        try:
            # Construct blob path
            blob_path = f"{self.raw_folder}/{video_filename}"
            blob = self.bucket.blob(blob_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.error(f"Video file not found: {blob_path}")
                return None
            
            # Generate local path if not provided
            if local_path is None:
                local_path = self.local_temp_dir / f"raw_{video_filename}"
            
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            logger.info(f"Downloading {blob_path} to {local_path}")
            blob.download_to_filename(str(local_path))
            
            # Verify download
            if local_path.exists() and local_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded {video_filename} ({local_path.stat().st_size} bytes)")
                return local_path
            else:
                logger.error(f"Download verification failed for {video_filename}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download {video_filename}: {e}")
            return None
    
    async def upload_processed_video(self, local_path: Path, 
                                   output_filename: Optional[str] = None,
                                   metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Upload a processed video to the processed-video-clips folder.
        
        Args:
            local_path: Path to local processed video file
            output_filename: Optional custom filename (uses local filename if None)
            metadata: Optional metadata to attach to the blob
            
        Returns:
            GCS path of uploaded file, None if failed
        """
        try:
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return None
            
            # Generate output filename if not provided
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"processed_{timestamp}_{local_path.name}"
            
            # Construct blob path
            blob_path = f"{self.processed_folder}/{output_filename}"
            blob = self.bucket.blob(blob_path)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Set content type
            if local_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
                blob.content_type = 'video/mp4'
            
            # Upload file
            logger.info(f"Uploading {local_path} to {blob_path}")
            blob.upload_from_filename(str(local_path))
            
            logger.info(f"Successfully uploaded processed video: {blob_path}")
            return blob_path
            
        except Exception as e:
            logger.error(f"Failed to upload processed video {local_path}: {e}")
            return None
    
    def _is_video_file(self, filename: str) -> bool:
        """Check if filename is a video file based on extension."""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
        return Path(filename).suffix.lower() in video_extensions
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files from temp-service-folder.
        
        Args:
            max_age_hours: Maximum age of files to keep (default: 24 hours)
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            blob_prefix = f"{self.temp_folder}/"
            blobs = self.bucket.list_blobs(prefix=blob_prefix)
            
            cleaned_count = 0
            for blob in blobs:
                if blob.time_created < cutoff_time:
                    blob.delete()
                    cleaned_count += 1
                    logger.debug(f"Deleted old temp file: {blob.name}")
            
            logger.info(f"Cleaned up {cleaned_count} temporary files older than {max_age_hours} hours")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for the bucket.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            stats = {
                'raw_videos': {'count': 0, 'total_size': 0},
                'processed_videos': {'count': 0, 'total_size': 0},
                'temp_files': {'count': 0, 'total_size': 0}
            }
            
            # Count files in each folder
            for folder, key in [(self.raw_folder, 'raw_videos'), 
                               (self.processed_folder, 'processed_videos'),
                               (self.temp_folder, 'temp_files')]:
                blobs = self.bucket.list_blobs(prefix=f"{folder}/")
                for blob in blobs:
                    if not blob.name.endswith('/'):  # Skip directory markers
                        stats[key]['count'] += 1
                        stats[key]['total_size'] += blob.size or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}

    async def upload_temp_file(self, local_path: Path,
                             temp_filename: Optional[str] = None) -> Optional[str]:
        """
        Upload a temporary file to temp-service-folder.

        Args:
            local_path: Path to local file
            temp_filename: Optional custom filename

        Returns:
            GCS path of uploaded file, None if failed
        """
        try:
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return None

            if temp_filename is None:
                temp_filename = local_path.name

            blob_path = f"{self.temp_folder}/{temp_filename}"
            blob = self.bucket.blob(blob_path)

            blob.upload_from_filename(str(local_path))
            logger.info(f"Uploaded temp file: {blob_path}")
            return blob_path

        except Exception as e:
            logger.error(f"Failed to upload temp file {local_path}: {e}")
            return None

    async def download_temp_file(self, temp_filename: str,
                               local_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download a temporary file from temp-service-folder.

        Args:
            temp_filename: Name of temp file
            local_path: Optional local path

        Returns:
            Path to downloaded file, None if failed
        """
        try:
            blob_path = f"{self.temp_folder}/{temp_filename}"
            blob = self.bucket.blob(blob_path)

            if not blob.exists():
                logger.error(f"Temp file not found: {blob_path}")
                return None

            if local_path is None:
                local_path = self.local_temp_dir / temp_filename

            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))

            logger.info(f"Downloaded temp file: {blob_path} to {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"Failed to download temp file {temp_filename}: {e}")
            return None

    def cleanup_local_temp(self) -> int:
        """
        Clean up local temporary files.

        Returns:
            Number of files cleaned up
        """
        try:
            cleaned_count = 0
            if self.local_temp_dir.exists():
                for file_path in self.local_temp_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Deleted local temp file: {file_path}")

            logger.info(f"Cleaned up {cleaned_count} local temporary files")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup local temp files: {e}")
            return 0


# Utility functions for Cloud Storage operations
async def batch_download_videos(storage_manager: CloudStorageManager,
                              video_filenames: List[str],
                              max_concurrent: int = 3) -> List[Tuple[str, Optional[Path]]]:
    """
    Download multiple videos concurrently.

    Args:
        storage_manager: CloudStorageManager instance
        video_filenames: List of video filenames to download
        max_concurrent: Maximum concurrent downloads

    Returns:
        List of tuples (filename, local_path or None)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def download_with_semaphore(filename: str) -> Tuple[str, Optional[Path]]:
        async with semaphore:
            local_path = await storage_manager.download_raw_video(filename)
            return filename, local_path

    tasks = [download_with_semaphore(filename) for filename in video_filenames]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and return results
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Download task failed: {result}")
        else:
            valid_results.append(result)

    return valid_results


def create_storage_manager(bucket_name: str = "bg-video-storage",
                         project_id: Optional[str] = None) -> CloudStorageManager:
    """
    Factory function to create and validate CloudStorageManager.

    Args:
        bucket_name: GCS bucket name
        project_id: GCP project ID

    Returns:
        Configured CloudStorageManager instance

    Raises:
        Exception: If connection to GCS fails
    """
    manager = CloudStorageManager(bucket_name=bucket_name, project_id=project_id)

    if not manager.check_connection():
        raise Exception(f"Failed to connect to Google Cloud Storage bucket: {bucket_name}")

    return manager
