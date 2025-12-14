#!/usr/bin/env python3
"""
Screenshot Manager for Supabase Storage
Handles screenshot upload, management, and retrieval
"""

import os
import uuid
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import aiohttp
from supabase import create_client, Client
from PIL import Image
import io

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ScreenshotMetadata:
    """Screenshot metadata"""
    local_path: str
    remote_url: Optional[str] = None
    file_size: int = 0
    file_hash: str = ""
    compressed: bool = False
    upload_status: str = "pending"  # pending, uploading, completed, failed
    upload_error: Optional[str] = None
    created_at: datetime = None
    uploaded_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ScreenshotManager:
    """Manages screenshot upload and retrieval with Supabase Storage"""

    def __init__(self, supabase_url: str, supabase_key: str, bucket_name: str = "AutoGLMStorage"):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.bucket_name = bucket_name

        # Initialize Supabase client
        self.client: Client = create_client(supabase_url, supabase_key)

        # Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.compression_quality = 85
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.webp'}

        # Async upload queue
        self.upload_queue: asyncio.Queue = asyncio.Queue()
        self.upload_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ScreenshotUpload")
        self.upload_tasks: Dict[str, asyncio.Task] = {}

        # Statistics
        self.stats = {
            'total_uploaded': 0,
            'total_failed': 0,
            'total_size_saved': 0,
            'compression_ratio': 0.0
        }

    async def upload_screenshot(self, local_path: str, task_id: str, step_id: Optional[str] = None) -> Optional[str]:
        """Upload a screenshot to Supabase Storage"""
        try:
            # Validate file
            if not os.path.exists(local_path):
                logger.error(f"Screenshot file not found: {local_path}")
                return None

            # Check file size
            file_size = os.path.getsize(local_path)
            if file_size > self.max_file_size:
                logger.warning(f"Screenshot too large: {file_size} bytes (max: {self.max_file_size})")
                # Try compression
                compressed_path = await self._compress_image(local_path)
                if compressed_path:
                    local_path = compressed_path
                    file_size = os.path.getsize(local_path)

            # Generate unique filename
            file_ext = Path(local_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"Unsupported file format: {file_ext}")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"screenshots/{task_id}/{timestamp}_{unique_id}{file_ext}"

            # Read file
            async with aiofiles.open(local_path, 'rb') as f:
                file_data = await f.read()

            # Upload to Supabase Storage
            try:
                # Get the storage client
                storage = self.client.storage

                # Upload file
                result = storage.from_(self.bucket_name).upload(
                    path=filename,
                    file=file_data,
                    file_options={
                        'content-type': self._get_content_type(file_ext)
                    }
                ).execute()

                if result.data:
                    # Get public URL
                    public_url_result = storage.from_(self.bucket_name).get_public_url(
                        filename
                    ).execute()

                    if public_url_result.data:
                        remote_url = public_url_result.data['publicUrl']
                        logger.info(f"Screenshot uploaded successfully: {filename} -> {remote_url}")

                        # Update statistics
                        self.stats['total_uploaded'] += 1
                        self.stats['total_size_saved'] += file_size

                        return remote_url
                    else:
                        logger.error("Failed to get public URL for uploaded file")
                        return None
                else:
                    logger.error("Failed to upload screenshot to Supabase Storage")
                    return None

            except Exception as e:
                logger.error(f"Error uploading to Supabase Storage: {e}")
                self.stats['total_failed'] += 1
                return None

        except Exception as e:
            logger.error(f"Error processing screenshot upload: {e}")
            return None

    async def _compress_image(self, image_path: str) -> Optional[str]:
        """Compress an image to reduce file size"""
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                # Compress in memory
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=self.compression_quality, optimize=True)
                compressed_data = output.getvalue()

                # Save compressed version
                compressed_path = image_path.replace(Path(image_path).suffix, '_compressed.jpg')
                async with aiofiles.open(compressed_path, 'wb') as f:
                    await f.write(compressed_data)

                original_size = os.path.getsize(image_path)
                compressed_size = len(compressed_data)
                compression_ratio = (original_size - compressed_size) / original_size

                logger.info(f"Image compressed: {original_size} -> {compressed_size} bytes ({compression_ratio:.1%} reduction)")

                # Update compression statistics
                if self.stats['compression_ratio'] == 0:
                    self.stats['compression_ratio'] = compression_ratio
                else:
                    self.stats['compression_ratio'] = (self.stats['compression_ratio'] + compression_ratio) / 2

                return compressed_path

        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            return None

    def _get_content_type(self, file_ext: str) -> str:
        """Get MIME content type for file extension"""
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        return content_types.get(file_ext.lower(), 'image/png')

    async def queue_upload(self, local_path: str, task_id: str, step_id: Optional[str] = None) -> str:
        """Queue a screenshot for async upload"""
        upload_id = str(uuid.uuid4())

        # Create metadata
        metadata = ScreenshotMetadata(
            local_path=local_path,
            file_size=os.path.getsize(local_path) if os.path.exists(local_path) else 0,
            file_hash=self._calculate_file_hash(local_path) if os.path.exists(local_path) else ""
        )

        # Add to queue
        await self.upload_queue.put({
            'upload_id': upload_id,
            'metadata': metadata,
            'task_id': task_id,
            'step_id': step_id
        })

        # Start upload task if not already running
        if 'main_uploader' not in self.upload_tasks:
            self.upload_tasks['main_uploader'] = asyncio.create_task(self._process_upload_queue())

        return upload_id

    async def _process_upload_queue(self):
        """Process the upload queue"""
        logger.info("Screenshot upload queue processor started")

        while True:
            try:
                # Get next upload item
                item = await self.upload_queue.get()

                # Process upload
                remote_url = await self.upload_screenshot(
                    item['metadata'].local_path,
                    item['task_id'],
                    item['step_id']
                )

                # Update metadata
                if remote_url:
                    item['metadata'].remote_url = remote_url
                    item['metadata'].upload_status = 'completed'
                    item['metadata'].uploaded_at = datetime.now()
                else:
                    item['metadata'].upload_status = 'failed'
                    item['metadata'].upload_error = 'Upload failed'

                # Update database record would go here
                # await self._update_screenshot_record(item)

                logger.info(f"Upload processed: {item['upload_id']} -> {item['metadata'].upload_status}")

            except Exception as e:
                logger.error(f"Error processing upload queue: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""

    async def batch_upload_existing_screenshots(self, screenshots_dir: str = "web/static/screenshots") -> Dict[str, Any]:
        """Batch upload existing screenshots"""
        screenshots_path = Path(screenshots_dir)
        if not screenshots_path.exists():
            logger.warning(f"Screenshots directory not found: {screenshots_dir}")
            return {'uploaded': 0, 'failed': 0, 'skipped': 0}

        results = {'uploaded': 0, 'failed': 0, 'skipped': 0}

        # Get all screenshot files
        screenshot_files = list(screenshots_path.glob("screenshot_*.png"))
        logger.info(f"Found {len(screenshot_files)} screenshots to upload")

        for screenshot_file in screenshot_files:
            try:
                # Extract task_id from filename (assuming format: screenshot_YYYYMMDD_HHMMSS_*.png)
                parts = screenshot_file.stem.split('_')
                if len(parts) >= 2:
                    # Generate a task_id from timestamp
                    task_id = f"legacy_task_{parts[1]}_{parts[2]}"
                else:
                    task_id = f"legacy_task_{screenshot_file.stem}"

                # Queue for upload
                await self.queue_upload(str(screenshot_file), task_id)
                results['uploaded'] += 1

            except Exception as e:
                logger.error(f"Error queueing screenshot {screenshot_file}: {e}")
                results['failed'] += 1

        return results

    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics"""
        return {
            **self.stats,
            'queue_size': self.upload_queue.qsize(),
            'active_tasks': len([t for t in self.upload_tasks.values() if not t.done()])
        }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up screenshot manager...")

        # Cancel upload tasks
        for task in self.upload_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.upload_tasks.values(), return_exceptions=True)

        # Shutdown executor
        self.upload_executor.shutdown(wait=True)

        logger.info("Screenshot manager cleanup completed")

# Global instance
_screenshot_manager: Optional[ScreenshotManager] = None

def get_screenshot_manager() -> Optional[ScreenshotManager]:
    """Get global screenshot manager instance"""
    global _screenshot_manager
    return _screenshot_manager

def init_screenshot_manager(supabase_url: str, supabase_key: str, bucket_name: str = "AutoGLMStorage") -> ScreenshotManager:
    """Initialize global screenshot manager"""
    global _screenshot_manager
    _screenshot_manager = ScreenshotManager(supabase_url, supabase_key, bucket_name)
    return _screenshot_manager