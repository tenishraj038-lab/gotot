import asyncio
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional

from celery import Task
from celery.utils.log import get_task_logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from . import celery_app

logger = get_task_logger(__name__)


def send_ws_progress(task_id: str, data: dict):
    try:
        import redis
        r = redis.Redis.from_url("redis://redis:6379/0", socket_connect_timeout=2)
        r.publish(f"progress:{task_id}", json.dumps(data))
        r.close()
    except Exception:
        pass


queue_meta: dict = {}


def update_queue_meta(task_id: str, status: str, progress: int = 0, message: str = ""):
    queue_meta[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": datetime.utcnow().isoformat(),
    }
    send_ws_progress(task_id, queue_meta[task_id])


class DownloadTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True


@celery_app.task(base=DownloadTask, name="process_download", queue="downloads")
def process_download(url: str, format_id: str, task_id: str, output_dir: str = "/tmp/downloads"):
    update_queue_meta(task_id, "queued", 0, "Task queued")

    try:
        from app.services.downloader import download_video

        update_queue_meta(task_id, "downloading", 10, "Downloading video...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(download_video(url, format_id, output_dir))
        loop.close()

        if not result:
            update_queue_meta(task_id, "error", 0, "Download failed")
            raise Exception(f"Download failed for {url}")

        update_queue_meta(task_id, "processing", 80, "Processing file...")

        file_size_mb = result.file_size / (1024 * 1024) if result.file_size else 0
        logger.info(f"Download completed: {result.file_name} ({file_size_mb:.1f} MB)")

        update_queue_meta(task_id, "completed", 100, "Download complete!")

        return {
            "task_id": task_id,
            "status": "completed",
            "file_name": result.file_name,
            "file_size": result.file_size,
            "format": result.format,
            "file_path": result.file_path,
        }
    except Exception as e:
        logger.error(f"Download task {task_id} failed: {e}")
        update_queue_meta(task_id, "error", 0, str(e))
        raise


@celery_app.task(name="process_batch_download", queue="downloads")
def process_batch_download(urls: list, format_id: str, task_id_prefix: str, output_dir: str = "/tmp/downloads"):
    results = []
    total = len(urls)
    for i, url in enumerate(urls):
        subtask_id = f"{task_id_prefix}_{i}"
        try:
            from app.services.downloader import download_video

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(download_video(url, format_id, output_dir))
            loop.close()

            if result:
                results.append({
                    "url": url,
                    "status": "completed",
                    "file_name": result.file_name,
                    "file_size": result.file_size,
                    "format": result.format,
                    "file_path": result.file_path,
                })
                update_queue_meta(subtask_id, "completed", 100, f"Downloaded {i+1}/{total}")
            else:
                results.append({"url": url, "status": "error", "detail": "Download failed"})
                update_queue_meta(subtask_id, "error", 0, f"Failed {i+1}/{total}")
        except Exception as e:
            results.append({"url": url, "status": "error", "detail": str(e)})
            update_queue_meta(subtask_id, "error", 0, str(e))

    return {"results": results, "total": total, "successful": sum(1 for r in results if r["status"] == "completed")}


@celery_app.task(name="process_mp3_conversion", queue="conversions")
def process_mp3_conversion(input_path: str, task_id: str, bitrate: str = "192"):
    update_queue_meta(task_id, "converting", 0, "Converting to MP3...")
    try:
        from app.services.downloader import convert_to_mp3

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(convert_to_mp3(input_path, bitrate))
        loop.close()

        if not result:
            update_queue_meta(task_id, "error", 0, "MP3 conversion failed")
            raise Exception("MP3 conversion failed")

        update_queue_meta(task_id, "completed", 100, "MP3 conversion complete!")
        return {
            "task_id": task_id,
            "status": "completed",
            "file_name": result.file_name,
            "file_size": result.file_size,
            "format": "mp3",
            "file_path": result.file_path,
        }
    except Exception as e:
        update_queue_meta(task_id, "error", 0, str(e))
        raise


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files():
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


def get_queue_status(task_id: str) -> Optional[dict]:
    return queue_meta.get(task_id)


celery_app.conf.beat_schedule = {
    "cleanup-downloads-every-hour": {
        "task": "cleanup_temp_files",
        "schedule": 3600.0,
    },
}
