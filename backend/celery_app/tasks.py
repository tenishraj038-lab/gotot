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
from app.config import get_settings

logger = get_task_logger(__name__)
dl_logger = logging.getLogger("gotot.download")

_settings = get_settings()

DOWNLOAD_STATUSES = ("queued", "downloading", "processing", "completed", "failed")


def send_ws_progress(task_id: str, data: dict):
    try:
        import redis
        r = redis.Redis.from_url(_settings.redis_url, socket_connect_timeout=2)
        r.publish(f"progress:{task_id}", json.dumps(data))
        r.close()
    except Exception:
        pass


queue_meta: dict = {}


def update_queue_meta(task_id: str, status: str, progress: int = 0, message: str = "", error: str = ""):
    entry = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": datetime.utcnow().isoformat(),
    }
    if error:
        entry["error"] = error
    if status == "failed":
        entry["failed_at"] = datetime.utcnow().isoformat()
    queue_meta[task_id] = entry
    send_ws_progress(task_id, entry)


def _is_transient_error(exception: Exception) -> bool:
    error_str = str(exception).lower()
    transient_keywords = (
        "timeout", "connection", "temporary", "retry", "unavailable",
        "rate limit", "429", "503", "502", "network",
    )
    return any(kw in error_str for kw in transient_keywords)


class DownloadTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        download_task_id = args[2] if len(args) > 2 else "unknown"
        url = args[0] if len(args) > 0 else "unknown"
        error_msg = str(exc)
        logger.error(f"Download task {download_task_id} permanently failed: {error_msg}")
        dl_logger.error("download_task_failed", extra={
            "task_id": download_task_id, "url": url, "error": error_msg,
        })
        update_queue_meta(download_task_id, "failed", 0, "Download permanently failed", error=error_msg)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        download_task_id = args[2] if len(args) > 2 else "unknown"
        logger.warning(f"Retrying download task {download_task_id}: {exc}")
        update_queue_meta(download_task_id, "queued", 0, f"Retrying after error: {str(exc)[:100]}")


@celery_app.task(base=DownloadTask, name="process_download", queue="downloads")
def process_download(url: str, format_id: str, task_id: str, output_dir: str = "/tmp/downloads"):
    update_queue_meta(task_id, "queued", 0, "Task queued")

    try:
        from app.services.downloader import download_video

        update_queue_meta(task_id, "downloading", 10, "Downloading video...")
        dl_logger.info("download_task_started", extra={"task_id": task_id, "url": url, "format": format_id})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(download_video(url, format_id, output_dir))
        finally:
            loop.close()

        if not result:
            update_queue_meta(task_id, "failed", 0, "Download failed", error="Download returned no result")
            dl_logger.error("download_task_empty_result", extra={"task_id": task_id, "url": url})
            raise Exception(f"Download returned no result for {url}")

        if not os.path.exists(result.file_path):
            update_queue_meta(task_id, "failed", 0, "Downloaded file missing", error="File missing after download")
            dl_logger.error("download_task_file_missing", extra={"task_id": task_id, "path": result.file_path})
            raise Exception(f"Downloaded file not found: {result.file_path}")

        update_queue_meta(task_id, "processing", 80, "Processing file...")

        file_size_mb = result.file_size / (1024 * 1024) if result.file_size else 0
        logger.info(f"Download completed: {result.file_name} ({file_size_mb:.1f} MB)")

        update_queue_meta(task_id, "completed", 100, "Download complete!")
        dl_logger.info("download_task_completed", extra={
            "task_id": task_id, "url": url, "file_size": result.file_size,
            "format": result.format, "file_name": result.file_name,
        })

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
        update_queue_meta(task_id, "failed", 0, str(e)[:200], error=str(e))
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
            try:
                result = loop.run_until_complete(download_video(url, format_id, output_dir))
            finally:
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
                update_queue_meta(subtask_id, "failed", 0, f"Failed {i+1}/{total}", error="Download failed")
        except Exception as e:
            logger.error(f"Batch subtask {subtask_id} failed: {e}")
            results.append({"url": url, "status": "error", "detail": str(e)[:200]})
            update_queue_meta(subtask_id, "failed", 0, str(e)[:200], error=str(e))

    return {"results": results, "total": total, "successful": sum(1 for r in results if r["status"] == "completed")}


@celery_app.task(name="process_mp3_conversion", queue="conversions")
def process_mp3_conversion(input_path: str, task_id: str, bitrate: str = "192"):
    update_queue_meta(task_id, "processing", 0, "Converting to MP3...")
    try:
        from app.services.downloader import convert_to_mp3

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(convert_to_mp3(input_path, bitrate))
        finally:
            loop.close()

        if not result:
            update_queue_meta(task_id, "failed", 0, "MP3 conversion failed", error="Conversion returned no result")
            raise Exception("MP3 conversion returned no result")

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
        update_queue_meta(task_id, "failed", 0, str(e)[:200], error=str(e))
        raise


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files():
    dl_logger.info("cleanup_started")

    download_dir = _settings.download_dir
    temp_dir = _settings.temp_dir
    retention_hours = _settings.file_retention_hours
    total_cleaned = 0

    for target_dir in (download_dir, temp_dir):
        if not os.path.exists(target_dir):
            dl_logger.info("cleanup_dir_skipped", extra={"dir": target_dir, "reason": "not_exists"})
            continue

        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        dir_cleaned = 0

        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                should_delete = mtime < cutoff

                if not should_delete:
                    continue

                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                dir_cleaned += 1
            except Exception as e:
                logger.error(f"Failed to clean up {item_path}: {e}")

        if dir_cleaned:
            dl_logger.info("cleanup_dir_completed", extra={"dir": target_dir, "cleaned": dir_cleaned})

        total_cleaned += dir_cleaned

    # Clean orphaned .part or .ytdl files that are stale
    for target_dir in (download_dir, temp_dir):
        if not os.path.exists(target_dir):
            continue
        for item in os.listdir(target_dir):
            if item.endswith((".part", ".ytdl", ".tmp", ".incomplete")):
                item_path = os.path.join(target_dir, item)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                    if mtime < datetime.utcnow() - timedelta(hours=max(1, retention_hours // 2)):
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                        total_cleaned += 1
                except Exception as e:
                    logger.error(f"Failed to clean orphaned file {item_path}: {e}")

    dl_logger.info("cleanup_completed", extra={"total_cleaned": total_cleaned})


def get_queue_status(task_id: str) -> Optional[dict]:
    return queue_meta.get(task_id)


celery_app.conf.beat_schedule = {
    "cleanup-downloads-hourly": {
        "task": "cleanup_temp_files",
        "schedule": _settings.cleanup_interval_seconds,
    },
}

