import asyncio
import json
import logging
from celery import Task
from celery.utils.log import get_task_logger
from . import celery_app

logger = get_task_logger(__name__)


def send_ws_progress(task_id: str, data: dict):
    try:
        import redis

        r = redis.Redis.from_url("redis://redis:6379/0")
        r.publish(f"progress:{task_id}", json.dumps(data))
        r.close()
    except Exception:
        pass


class DownloadTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True


@celery_app.task(base=DownloadTask, name="process_download")
def process_download(url: str, format_id: str, task_id: str):
    logger.info(f"Processing download task {task_id}: {url}")
    send_ws_progress(task_id, {"status": "processing", "progress": 0, "message": "Starting download..."})
    try:
        from app.services.downloader import download_video

        send_ws_progress(task_id, {"status": "downloading", "progress": 25, "message": "Downloading video..."})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(download_video(url, format_id))
        loop.close()

        if not result:
            send_ws_progress(task_id, {"status": "error", "progress": 0, "message": "Download failed"})
            raise Exception(f"Download failed for {url}")

        send_ws_progress(task_id, {"status": "completed", "progress": 100, "message": "Download complete!"})

        logger.info(f"Download completed: {result.file_name}")
        return {
            "task_id": task_id,
            "status": "completed",
            "file_name": result.file_name,
            "file_size": result.file_size,
            "format": result.format,
        }
    except Exception as e:
        logger.error(f"Download task failed: {e}")
        send_ws_progress(task_id, {"status": "error", "progress": 0, "message": str(e)})
        raise


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files():
    import shutil
    import os
    from datetime import datetime, timedelta

    download_dir = "/tmp/downloads"
    if not os.path.exists(download_dir):
        return

    cutoff = datetime.utcnow() - timedelta(hours=1)
    cleaned = 0

    for item in os.listdir(download_dir):
        item_path = os.path.join(download_dir, item)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            if mtime < cutoff:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                cleaned += 1
        except Exception as e:
            logger.error(f"Failed to clean up {item_path}: {e}")

    if cleaned:
        logger.info(f"Cleaned up {cleaned} expired files from {download_dir}")


celery_app.conf.beat_schedule = {
    "cleanup-downloads-every-hour": {
        "task": "cleanup_temp_files",
        "schedule": 3600.0,
    },
}
