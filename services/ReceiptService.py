import os
from datetime import datetime, timedelta
from typing import List
from services.ReceiptApiClient import ReceiptApiClient
import logging
from pytz import utc


# Directory containing bills to process
BILLS_DIRECTORY = os.environ.get("BILLS_DIRECTORY", "./bills")

# Initialize logger
logger = logging.getLogger(__name__)

async def upload_bills_job():
    """
    Job to upload all JPG and PNG files from the bills directory.
    Files are removed after successful upload.
    """
    file_paths = []
    
    # Find all jpg and png files in the directory
    for filename in os.listdir(BILLS_DIRECTORY):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_path = os.path.join(BILLS_DIRECTORY, filename)
            file_paths.append(file_path)
    
    if not file_paths:
        logger.info(f"No bill files found in {BILLS_DIRECTORY}")
        return
    
    try:
        logger.info(f"Attempting to upload {len(file_paths)} bills")
        async with ReceiptApiClient(
            base_url="https://receipt-analyser-api:8082",
            verify_ssl=False) as service:
            try:
                # Open files only when needed
                with [open(fp, 'rb') for fp in file_paths] as bill_files:
                    await service.upload_receipts(bill_files)
                logger.info(f"Uploaded {len(file_paths)}")
                
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

async def send_weekly_report_job():
    """
    Job to send a weekly report by email for the previous week.
    Covers period from Monday 00:01 to Sunday 23:59
    """
    today = datetime.now(utc)  # Use UTC timezone
    
    # Calculate first and last day of current week
    current_week_monday = today - timedelta(days=today.weekday())
    
    # Get previous week's dates
    first_day = current_week_monday  # Previous Monday
    last_day = today  # Next Sunday
    
    # Set precise times
    first_day = first_day.replace(hour=0, minute=1, second=0, microsecond=0)
    last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=0)
    
    try:
        async with ReceiptApiClient(
            base_url="https://receipt-analyser-api:8082",
            verify_ssl=False) as service:
            result = await service.send_report_by_email(first_day, last_day)
            logger.info(f"Sent weekly report for {first_day.strftime('%d %b %H:%M')} - {last_day.strftime('%d %b %Y %H:%M')}: {result}")
    except Exception as e:
        logger.error(f"Error sending weekly report: {str(e)}")