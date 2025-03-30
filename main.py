from fastapi import FastAPI
import uvicorn
import os
from contextlib import asynccontextmanager
from Utilities.LogConfiguration import LogConfig
from Utilities.LogData import LogData
from loguru import logger
from services.Schedulers import schedule_jobs, scheduler, shutdown_scheduler, upload_bills_job, send_weekly_report_job
from services.ReceiptApiService import ReceiptApiService
from datetime import datetime, timedelta

# Configure logging
log_data = LogData(
    level = "INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    pathToFile="logs/app.log",
    rotation="10 MB",
    retention="1 week"
)

LogConfig.setLogging(log_data)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎬 Application starting...")
    
    # Check if jobs exist and schedule them if they don't
    
    if not scheduler.get_jobs():
        logger.info("No scheduled jobs found. Setting up scheduler jobs...")
        schedule_jobs()
    else:
        jobs = scheduler.get_jobs(
            jobstore="default"
        )
        logger.info(f"Found {len(jobs)} existing scheduled jobs")
        for job in jobs:
            logger.info(f"Scheduled job: {job.id} - Next run: {job.next_run_time}")
    
    yield
    
    #Shutdown the scheduler when the application stops
    logger.info("Shutting down scheduler...")
    shutdown_scheduler()
    logger.info("🛑 Application shutting down...")

app = FastAPI(lifespan=lifespan)

async def version():
    return {"version": "1.0.0"}

async def trigger_upload_bills():
    """Endpoint to manually trigger the bill upload job"""
    logger.info("Manually triggering bill upload job")
    await upload_bills_job()
    return {"message": "Bill upload job completed"}

async def trigger_weekly_report():
    """Endpoint to manually trigger the weekly report job"""
    logger.info("Manually triggering weekly report job")
    await send_weekly_report_job()
    return {"message": "Weekly report job completed"}

app.add_api_route("/", version, methods=["GET"])
app.add_api_route("/trigger-upload", trigger_upload_bills, methods=["POST"])
app.add_api_route("/trigger-report", trigger_weekly_report, methods=["POST"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")