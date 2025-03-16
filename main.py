from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from Utilities.LogConfiguration import LogConfig
from Utilities.LogData import LogData
from loguru import logger
from services.Schedulers import schedule_jobs, scheduler, shutdown_scheduler


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
        jobs = scheduler.get_jobs()
        logger.info(f"Found {len(jobs)} existing scheduled jobs")
        for job in jobs:
            logger.info(f"Scheduled job: {job.id} - Next run: {job.next_run_time}")
    
    yield
    
    # Shutdown the scheduler when the application stops
    logger.info("Shutting down scheduler...")
    shutdown_scheduler()
    logger.info("🛑 Application shutting down...")

app = FastAPI(lifespan=lifespan)
async def version():
    return {"version": "1.0.0"}

app.add_api_route("/", version, methods=["GET"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")