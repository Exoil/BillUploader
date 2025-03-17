from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.redis import RedisJobStore
import os
import asyncio
from datetime import datetime, timedelta
from typing import List
from services.ReceiptApiService import ReceiptApiService
import logging

jobstores = {
    "default": RedisJobStore(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        db=0
    )
}

# Initialize scheduler with Redis
scheduler = BackgroundScheduler(jobstores=jobstores)

# Directory containing bills to process
BILLS_DIRECTORY = os.environ.get("BILLS_DIRECTORY", "./bills")

# Initialize logger
logger = logging.getLogger(__name__)

async def upload_bills_job():
    """
    Job to upload all JPG and PNG files from the bills directory.
    Files are removed after successful upload.
    """
    bill_files = []
    file_paths = []
    
    # Find all jpg and png files in the directory
    for filename in os.listdir(BILLS_DIRECTORY):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_path = os.path.join(BILLS_DIRECTORY, filename)
            file_paths.append(file_path)
            bill_files.append(open(file_path, 'rb'))
    
    if not bill_files:
        logger.info(f"No bill files found in {BILLS_DIRECTORY}")
        return
    
    try:
        logger.info(f"Attempting to upload {len(bill_files)} bills")
        async with ReceiptApiService(verify_ssl=False) as service:
            try:
                await service.upload_receipts(bill_files)
                logger.info(f"Uploaded {len(bill_files)}")
                
                # Remove files after successful upload
                for file_path in file_paths:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error in upload_receipts method: {str(e)}", exc_info=True)
                raise
    except Exception as e:
        logger.error(f"Error uploading bills: {str(e)}", exc_info=True)
    finally:
        # Close all opened files
        for file in bill_files:
            file.close()

async def send_weekly_report_job():
    """
    Job to send a weekly report by email for the previous week.
    """
    today = datetime.now()
    # Calculate first and last day of previous week (Monday to Sunday)
    last_day = today - timedelta(days=today.weekday() + 1)  # Previous Sunday
    first_day = last_day - timedelta(days=6)  # Previous Monday
    
    try:
        async with ReceiptApiService(verify_ssl=False) as service:
            result = await service.send_report_by_email(first_day, last_day)
            logger.info(f"Sent weekly report for {first_day.strftime('%d %b')} - {last_day.strftime('%d %b %Y')}: {result}")
    except Exception as e:
        logger.error(f"Error sending weekly report: {str(e)}")

def run_async_job(coroutine):
    """Helper function to run async jobs in the scheduler."""
    asyncio.run(coroutine())

# Named functions for scheduler jobs instead of lambdas
def run_upload_bills_job():
    """Wrapper function for upload_bills_job to be used with scheduler"""
    run_async_job(upload_bills_job)

def run_weekly_report_job():
    """Wrapper function for send_weekly_report_job to be used with scheduler"""
    run_async_job(send_weekly_report_job)

def schedule_jobs():
    """
    Schedule all jobs and start the scheduler.
    """
    # Schedule bill upload job to run daily at 10 PM
    scheduler.add_job(
        run_upload_bills_job,
        CronTrigger(hour=22, minute=0),
        id="upload_bills_job",
        replace_existing=True
    )
    
    # Schedule weekly report job to run every Sunday at 1 PM
    scheduler.add_job(
        run_weekly_report_job,
        CronTrigger(day_of_week='sun', hour=13, minute=0),
        id="send_weekly_report_job",
        replace_existing=True
    )
    
    # Start the scheduler if it's not already running
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with jobs configured")

def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")
