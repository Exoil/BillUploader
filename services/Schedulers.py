from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.redis import RedisJobStore
import os
import asyncio
from datetime import datetime, timedelta
from typing import List
from services.ReceiptApiService import ReceiptApiService

jobstores = {
    "default": RedisJobStore(host="localhost", port=6379, db=0)
}

# Initialize scheduler with Redis
scheduler = BackgroundScheduler(jobstores=jobstores)

# Directory containing bills to process
BILLS_DIRECTORY = os.environ.get("BILLS_DIRECTORY", "./bills")

async def upload_bills_job():
    """
    Job to upload all JPG and PNG files from the bills directory.
    """
    bill_files = []
    
    # Find all jpg and png files in the directory
    for filename in os.listdir(BILLS_DIRECTORY):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_path = os.path.join(BILLS_DIRECTORY, filename)
            bill_files.append(open(file_path, 'rb'))
    
    if not bill_files:
        print(f"No bill files found in {BILLS_DIRECTORY}")
        return
    
    try:
        async with ReceiptApiService() as service:
            result = await service.upload_receipts(bill_files)
            print(f"Uploaded {len(bill_files)} bills: {result}")
    except Exception as e:
        print(f"Error uploading bills: {str(e)}")
    finally:
        # Close all opened files
        for file in bill_files:
            file.close()

async def send_monthly_report_job():
    """
    Job to send a monthly report by email for the previous month.
    """
    today = datetime.now()
    # Calculate first and last day of previous month
    first_day = datetime(today.year, today.month, 1) - timedelta(days=1)
    first_day = datetime(first_day.year, first_day.month, 1)
    last_day = datetime(today.year, today.month, 1) - timedelta(days=1)
    
    try:
        async with ReceiptApiService() as service:
            result = await service.send_report_by_email(first_day, last_day)
            print(f"Sent monthly report for {first_day.strftime('%B %Y')}: {result}")
    except Exception as e:
        print(f"Error sending monthly report: {str(e)}")

def run_async_job(coroutine):
    """Helper function to run async jobs in the scheduler."""
    asyncio.run(coroutine())

def schedule_jobs():
    """
    Schedule all jobs and start the scheduler.
    """
    # Schedule bill upload job to run daily at 10 PM
    scheduler.add_job(
        lambda: run_async_job(upload_bills_job),
        CronTrigger(hour=22, minute=0),
        id="upload_bills_job",
        replace_existing=True
    )
    
    # Schedule monthly report job to run on the 1st of each month at 1 AM
    scheduler.add_job(
        lambda: run_async_job(send_monthly_report_job),
        CronTrigger(day=1, hour=1, minute=0),
        id="send_monthly_report_job",
        replace_existing=True
    )
    
    # Start the scheduler if it's not already running
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started with jobs configured")

def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully.
    """
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shutdown complete")
