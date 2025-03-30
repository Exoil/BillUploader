from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.redis import RedisJobStore
import os
import asyncio
from datetime import datetime, timedelta
from typing import List
from services.ReceiptApiService import ReceiptApiService
import logging
from pytz import utc

jobstores = {
    "default": RedisJobStore(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        db=0
    )
}

# Initialize scheduler with Redis and explicit UTC timezone
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    timezone=utc  # Explicitly set UTC timezone
)

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
        async with ReceiptApiService(
            base_url="https://receipt-analyser-api:8082",
            verify_ssl=False) as service:
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
        async with ReceiptApiService(
            base_url="https://receipt-analyser-api:8082",
            verify_ssl=False) as service:
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

def initialize_scheduler():
    """Initialize and verify scheduler connection"""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started successfully")
        
        # Test Redis connection
        scheduler.get_jobs()  # This will throw an exception if Redis is not accessible
        logger.info("Successfully connected to Redis jobstore")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {str(e)}")
        return False

def schedule_jobs():
    """
    Schedule all jobs and start the scheduler.
    """
    try:
        # Schedule bill upload job to run every 2 hours
        upload_job = scheduler.add_job(
            run_upload_bills_job,
            CronTrigger(hour='*/2', minute=0, timezone=utc),  # Explicit UTC
            id="upload_bills_job",
            replace_existing=True
        )
        logger.info(f"Scheduled upload_bills_job - Next run at: {upload_job.next_run_time} UTC")
        
        # Schedule weekly report job to run every Sunday at 1 PM UTC
        report_job = scheduler.add_job(
            run_weekly_report_job,
            CronTrigger(day_of_week='sun', hour=13, minute=0, timezone=utc),  # Explicit UTC
            id="send_weekly_report_job",
            replace_existing=True
        )
        logger.info(f"Scheduled send_weekly_report_job - Next run at: {report_job.next_run_time} UTC")
        
    except Exception as e:
        logger.error(f"Error scheduling jobs: {str(e)}")
        raise

def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")
