#!/usr/bin/env python3
"""
批量上传截图到 Supabase Storage 的工具
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from web.screenshot_manager import get_screenshot_manager, init_screenshot_manager
from web.supabase_manager import SupabaseTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def bulk_upload_screenshots(screenshots_dir: str, task_prefix: str = "bulk_upload"):
    """批量上传截图"""

    # Initialize screenshot manager
    try:
        from dotenv import load_dotenv
        load_dotenv()

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')

        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase configuration. Please check SUPABASE_URL and SUPABASE_SECRET_KEY")
            return False

        screenshot_manager = init_screenshot_manager(supabase_url, supabase_key)
        logger.info("Screenshot manager initialized")

    except Exception as e:
        logger.error(f"Failed to initialize screenshot manager: {e}")
        return False

    # Get all screenshot files
    screenshots_path = Path(screenshots_dir)
    if not screenshots_path.exists():
        logger.error(f"Screenshots directory not found: {screenshots_dir}")
        return False

    # Find all PNG files
    screenshot_files = list(screenshots_path.glob("*.png"))
    logger.info(f"Found {len(screenshot_files)} screenshots to upload")

    if not screenshot_files:
        logger.info("No screenshots found to upload")
        return True

    # Upload results
    results = {
        'total': len(screenshot_files),
        'uploaded': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }

    # Process each screenshot
    for i, screenshot_file in enumerate(screenshot_files, 1):
        try:
            logger.info(f"Processing {i}/{len(screenshot_files)}: {screenshot_file.name}")

            # Generate task_id from filename
            filename_parts = screenshot_file.stem.split('_')
            if len(filename_parts) >= 2:
                timestamp = '_'.join(filename_parts[1:3])  # Join date and time
                task_id = f"{task_prefix}_{timestamp}"
            else:
                task_id = f"{task_prefix}_{screenshot_file.stem}"

            # Upload screenshot
            remote_url = await screenshot_manager.upload_screenshot(
                str(screenshot_file),
                task_id
            )

            if remote_url:
                logger.info(f"✅ Uploaded: {screenshot_file.name} -> {remote_url}")
                results['uploaded'] += 1

                # Update database record
                if update_database_record(str(screenshot_file), remote_url, task_id):
                    logger.info(f"✅ Database updated: {screenshot_file.name}")
                else:
                    logger.warning(f"⚠️  Database update failed: {screenshot_file.name}")
            else:
                logger.error(f"❌ Upload failed: {screenshot_file.name}")
                results['failed'] += 1
                results['errors'].append(f"Failed to upload {screenshot_file.name}")

        except Exception as e:
            logger.error(f"❌ Error processing {screenshot_file.name}: {e}")
            results['failed'] += 1
            results['errors'].append(f"Error processing {screenshot_file.name}: {str(e)}")

    # Print summary
    logger.info("\n" + "="*50)
    logger.info("UPLOAD SUMMARY")
    logger.info("="*50)
    logger.info(f"Total screenshots: {results['total']}")
    logger.info(f"Successfully uploaded: {results['uploaded']}")
    logger.info(f"Failed to upload: {results['failed']}")
    logger.info(f"Skipped: {results['skipped']}")

    if results['errors']:
        logger.info("\nErrors:")
        for error in results['errors']:
            logger.info(f"  - {error}")

    # Print statistics
    stats = screenshot_manager.get_upload_statistics()
    logger.info(f"\nUpload Statistics:")
    logger.info(f"  Total uploaded: {stats.get('total_uploaded', 0)}")
    logger.info(f"  Total failed: {stats.get('total_failed', 0)}")
    logger.info(f"  Queue size: {stats.get('queue_size', 0)}")
    logger.info(f"  Active tasks: {stats.get('active_tasks', 0)}")

    return results['failed'] == 0

def update_database_record(local_path: str, remote_url: str, task_id: str) -> bool:
    """更新数据库记录"""
    try:
        # Initialize SupabaseTaskManager
        task_manager = SupabaseTaskManager()

        # Find steps that reference this screenshot
        steps = task_manager.get_task_steps(task_id)

        updated = False
        for step in steps:
            if step.get('screenshot_path') == local_path:
                # Update step with remote URL
                success = task_manager.update_task(
                    step['id'],  # Use step_id
                    screenshot_url=remote_url
                )

                if success:
                    updated = True
                    logger.debug(f"Updated step {step['id']} with remote URL")

        return updated

    except Exception as e:
        logger.error(f"Error updating database record: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Batch upload screenshots to Supabase Storage')
    parser.add_argument(
        '--screenshots-dir',
        default='web/static/screenshots',
        help='Screenshots directory path (default: web/static/screenshots)'
    )
    parser.add_argument(
        '--task-prefix',
        default='bulk_upload',
        help='Task ID prefix for uploaded screenshots (default: bulk_upload)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )

    args = parser.parse_args()

    if args.dry_run:
        screenshots_path = Path(args.screenshots_dir)
        if screenshots_path.exists():
            screenshot_files = list(screenshots_path.glob("*.png"))
            logger.info(f"DRY RUN: Would upload {len(screenshot_files)} screenshots from {screenshots_path}")
            for f in screenshot_files[:5]:  # Show first 5
                logger.info(f"  - {f.name}")
            if len(screenshot_files) > 5:
                logger.info(f"  ... and {len(screenshot_files) - 5} more")
        else:
            logger.error(f"Screenshots directory not found: {screenshots_path}")
        return

    # Run the upload
    try:
        success = asyncio.run(bulk_upload_screenshots(args.screenshots_dir, args.task_prefix))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nUpload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()