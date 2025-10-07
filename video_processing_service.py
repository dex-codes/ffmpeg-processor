"""
Cloud-native video processing service for Google Cloud Run.

This service integrates the existing video processing pipeline with Google Cloud Storage,
providing a scalable solution for processing videos in the cloud.

Key features:
- Download videos from GCS raw-video-clips folder
- Process videos using existing FFmpeg pipeline
- Upload results to GCS processed-video-clips folder
- Manage temporary files in GCS temp-service-folder
- Async processing with proper error handling

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import logging
import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import subprocess

# Import existing video processing modules
from video_processor import (
    convert_video_format, 
    convert_videos_parallel, 
    concatenate_videos,
    process_video_sequence
)
from video_config import VIDEO_PRESETS, CODEC_PRESETS, PROCESSING_DEFAULTS
from cloud_storage import CloudStorageManager, batch_download_videos

logger = logging.getLogger(__name__)


class VideoProcessingService:
    """
    Cloud-native video processing service that integrates with Google Cloud Storage.
    """
    
    def __init__(self, storage_manager: CloudStorageManager):
        """
        Initialize the video processing service.
        
        Args:
            storage_manager: CloudStorageManager instance for GCS operations
        """
        self.storage = storage_manager
        self.job_id = None
        self.processing_stats = {
            'jobs_processed': 0,
            'videos_processed': 0,
            'total_processing_time': 0,
            'errors': 0
        }
        
        # Create local working directory
        self.work_dir = Path(tempfile.gettempdir()) / "video_processing_service"
        self.work_dir.mkdir(exist_ok=True)
        
        logger.info("VideoProcessingService initialized")
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def process_single_video(self, 
                                 video_filename: str,
                                 preset: str = "mobile_vertical",
                                 custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a single video from raw-video-clips to processed-video-clips.
        
        Args:
            video_filename: Name of video file in raw-video-clips folder
            preset: Video processing preset name
            custom_settings: Optional custom processing settings
            
        Returns:
            Processing result dictionary
        """
        job_id = self._generate_job_id()
        self.job_id = job_id
        start_time = datetime.now()
        
        result = {
            'job_id': job_id,
            'status': 'started',
            'video_filename': video_filename,
            'preset': preset,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'processing_time_seconds': None,
            'input_file_size': None,
            'output_file_size': None,
            'output_gcs_path': None,
            'error': None
        }
        
        try:
            logger.info(f"Starting video processing job {job_id} for {video_filename}")
            
            # Check FFmpeg availability
            if not self._check_ffmpeg():
                raise Exception("FFmpeg not available")
            
            # Get processing settings
            if custom_settings:
                settings = custom_settings
            else:
                if preset not in VIDEO_PRESETS:
                    raise ValueError(f"Unknown preset: {preset}")
                settings = VIDEO_PRESETS[preset].copy()
            
            # Step 1: Download video from GCS
            logger.info(f"Downloading {video_filename} from GCS")
            local_input_path = await self.storage.download_raw_video(video_filename)
            
            if local_input_path is None:
                raise Exception(f"Failed to download video: {video_filename}")
            
            result['input_file_size'] = local_input_path.stat().st_size
            
            # Step 2: Process video
            logger.info(f"Processing video with preset: {preset}")
            output_filename = f"processed_{job_id}_{video_filename}"
            local_output_path = self.work_dir / output_filename
            
            # Use existing video processing function
            processed_path = convert_video_format(
                input_file=str(local_input_path),
                output_file=str(local_output_path),
                frame_width=settings.get('frame_width', 1080),
                frame_height=settings.get('frame_height', 1920),
                frame_rate=settings.get('frame_rate', 30),
                bitrate=settings.get('bitrate', '6M')
            )
            
            if processed_path is None:
                raise Exception("Video processing failed")
            
            result['output_file_size'] = local_output_path.stat().st_size
            
            # Step 3: Upload processed video to GCS
            logger.info(f"Uploading processed video to GCS")
            metadata = {
                'job_id': job_id,
                'original_filename': video_filename,
                'preset': preset,
                'processing_date': datetime.now().isoformat()
            }
            
            gcs_output_path = await self.storage.upload_processed_video(
                local_path=local_output_path,
                output_filename=output_filename,
                metadata=metadata
            )
            
            if gcs_output_path is None:
                raise Exception("Failed to upload processed video")
            
            result['output_gcs_path'] = gcs_output_path
            result['status'] = 'completed'
            
            # Step 4: Cleanup local files
            if local_input_path.exists():
                local_input_path.unlink()
            if local_output_path.exists():
                local_output_path.unlink()
            
            logger.info(f"Successfully completed job {job_id}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            self.processing_stats['errors'] += 1
            
            # Cleanup on error
            try:
                if 'local_input_path' in locals() and local_input_path.exists():
                    local_input_path.unlink()
                if 'local_output_path' in locals() and local_output_path.exists():
                    local_output_path.unlink()
            except:
                pass
        
        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['processing_time_seconds'] = (end_time - start_time).total_seconds()
            
            # Update stats
            self.processing_stats['jobs_processed'] += 1
            if result['status'] == 'completed':
                self.processing_stats['videos_processed'] += 1
            self.processing_stats['total_processing_time'] += result['processing_time_seconds']
        
        return result
    
    async def process_video_batch(self, 
                                video_filenames: List[str],
                                preset: str = "mobile_vertical",
                                max_concurrent: int = 2) -> Dict[str, Any]:
        """
        Process multiple videos concurrently.
        
        Args:
            video_filenames: List of video filenames to process
            preset: Video processing preset name
            max_concurrent: Maximum concurrent processing jobs
            
        Returns:
            Batch processing result dictionary
        """
        job_id = self._generate_job_id()
        start_time = datetime.now()
        
        result = {
            'batch_job_id': job_id,
            'status': 'started',
            'total_videos': len(video_filenames),
            'preset': preset,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'processing_time_seconds': None,
            'successful_videos': 0,
            'failed_videos': 0,
            'results': [],
            'error': None
        }
        
        try:
            logger.info(f"Starting batch processing job {job_id} for {len(video_filenames)} videos")
            
            # Process videos with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(filename: str) -> Dict[str, Any]:
                async with semaphore:
                    return await self.process_single_video(filename, preset)
            
            # Execute all processing tasks
            tasks = [process_with_semaphore(filename) for filename in video_filenames]
            individual_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, individual_result in enumerate(individual_results):
                if isinstance(individual_result, Exception):
                    error_result = {
                        'job_id': f"error_{i}",
                        'status': 'failed',
                        'video_filename': video_filenames[i],
                        'error': str(individual_result)
                    }
                    result['results'].append(error_result)
                    result['failed_videos'] += 1
                else:
                    result['results'].append(individual_result)
                    if individual_result['status'] == 'completed':
                        result['successful_videos'] += 1
                    else:
                        result['failed_videos'] += 1
            
            result['status'] = 'completed'
            logger.info(f"Batch job {job_id} completed: {result['successful_videos']} successful, {result['failed_videos']} failed")
            
        except Exception as e:
            logger.error(f"Batch job {job_id} failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['processing_time_seconds'] = (end_time - start_time).total_seconds()

        return result

    async def process_video_sequence(self,
                                   video_filenames: List[str],
                                   output_filename: str,
                                   preset: str = "mobile_vertical",
                                   custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process and concatenate multiple videos into a single output video.

        Args:
            video_filenames: List of video filenames in desired order
            output_filename: Name for the final concatenated video
            preset: Video processing preset name
            custom_settings: Optional custom processing settings

        Returns:
            Sequence processing result dictionary
        """
        job_id = self._generate_job_id()
        start_time = datetime.now()

        result = {
            'sequence_job_id': job_id,
            'status': 'started',
            'input_videos': video_filenames,
            'output_filename': output_filename,
            'preset': preset,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'processing_time_seconds': None,
            'total_input_size': 0,
            'output_file_size': None,
            'output_gcs_path': None,
            'error': None
        }

        local_files = []

        try:
            logger.info(f"Starting sequence processing job {job_id} for {len(video_filenames)} videos")

            # Check FFmpeg availability
            if not self._check_ffmpeg():
                raise Exception("FFmpeg not available")

            # Get processing settings
            if custom_settings:
                settings = custom_settings
            else:
                if preset not in VIDEO_PRESETS:
                    raise ValueError(f"Unknown preset: {preset}")
                settings = VIDEO_PRESETS[preset].copy()

            # Step 1: Download all videos concurrently
            logger.info("Downloading videos from GCS")
            download_results = await batch_download_videos(
                self.storage,
                video_filenames,
                max_concurrent=3
            )

            # Collect successfully downloaded files
            for filename, local_path in download_results:
                if local_path is not None:
                    local_files.append(str(local_path))
                    result['total_input_size'] += local_path.stat().st_size
                else:
                    logger.warning(f"Failed to download {filename}")

            if not local_files:
                raise Exception("No videos were successfully downloaded")

            logger.info(f"Successfully downloaded {len(local_files)}/{len(video_filenames)} videos")

            # Step 2: Process video sequence using existing pipeline
            final_output_path = self.work_dir / f"sequence_{job_id}_{output_filename}"

            success = process_video_sequence(
                input_files=local_files,
                output_file=str(final_output_path),
                frame_width=settings.get('frame_width', 1080),
                frame_height=settings.get('frame_height', 1920),
                frame_rate=settings.get('frame_rate', 30),
                bitrate=settings.get('bitrate', '6M'),
                max_workers=settings.get('max_workers', 2)  # Limit for Cloud Run
            )

            if not success or not final_output_path.exists():
                raise Exception("Video sequence processing failed")

            result['output_file_size'] = final_output_path.stat().st_size

            # Step 3: Upload final video to GCS
            logger.info("Uploading final sequence video to GCS")
            metadata = {
                'sequence_job_id': job_id,
                'input_videos': ','.join(video_filenames),
                'preset': preset,
                'processing_date': datetime.now().isoformat(),
                'video_count': str(len(local_files))
            }

            gcs_output_path = await self.storage.upload_processed_video(
                local_path=final_output_path,
                output_filename=f"sequence_{output_filename}",
                metadata=metadata
            )

            if gcs_output_path is None:
                raise Exception("Failed to upload final sequence video")

            result['output_gcs_path'] = gcs_output_path
            result['status'] = 'completed'

            logger.info(f"Successfully completed sequence job {job_id}")

        except Exception as e:
            logger.error(f"Sequence job {job_id} failed: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            self.processing_stats['errors'] += 1

        finally:
            # Cleanup all local files
            for local_file in local_files:
                try:
                    Path(local_file).unlink()
                except:
                    pass

            # Cleanup final output
            try:
                if 'final_output_path' in locals() and final_output_path.exists():
                    final_output_path.unlink()
            except:
                pass

            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['processing_time_seconds'] = (end_time - start_time).total_seconds()

            # Update stats
            self.processing_stats['jobs_processed'] += 1
            if result['status'] == 'completed':
                self.processing_stats['videos_processed'] += len(video_filenames)
            self.processing_stats['total_processing_time'] += result['processing_time_seconds']

        return result

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_stats.copy()

    def get_available_presets(self) -> Dict[str, Any]:
        """Get available video processing presets."""
        return {
            'presets': VIDEO_PRESETS,
            'codec_presets': CODEC_PRESETS,
            'defaults': PROCESSING_DEFAULTS
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the service."""
        health = {
            'status': 'healthy',
            'ffmpeg_available': self._check_ffmpeg(),
            'gcs_connection': self.storage.check_connection(),
            'local_temp_dir': str(self.work_dir),
            'temp_dir_writable': os.access(self.work_dir, os.W_OK),
            'processing_stats': self.get_processing_stats()
        }

        # Overall health status
        if not health['ffmpeg_available'] or not health['gcs_connection'] or not health['temp_dir_writable']:
            health['status'] = 'unhealthy'

        return health

    async def cleanup_old_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up old temporary files both locally and in GCS.

        Args:
            max_age_hours: Maximum age of files to keep

        Returns:
            Cleanup statistics
        """
        local_cleaned = self.storage.cleanup_local_temp()
        gcs_cleaned = await self.storage.cleanup_temp_files(max_age_hours)

        return {
            'local_files_cleaned': local_cleaned,
            'gcs_files_cleaned': gcs_cleaned
        }
