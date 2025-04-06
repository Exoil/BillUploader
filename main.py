from fastapi import FastAPI, HTTPException
import uvicorn
from contextlib import asynccontextmanager
from Utilities.LogConfiguration import LogConfig
from Utilities.LogData import LogData
from loguru import logger
from services.ReceiptService import (
    upload_bills_job, 
    send_weekly_report_job
)
from services.ReceiptApiClient import ReceiptApiClient
from datetime import datetime, timedelta
from pytz import utc

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
    
    
    yield
    logger.info("🛑 Application shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/", tags=["System"])
async def version() -> dict[str, str]:
    """Get the current API version
    
    Returns:
        dict: Version information
    """
    return {"version": "1.0.0"}

@app.post("/trigger-upload", tags=["Jobs"])
async def trigger_upload_bills() -> dict[str, str]:
    """Manually trigger the bill upload job
    
    Returns:
        dict: Job completion status message
    
    Raises:
        HTTPException: If the job fails to execute
    """
    try:
        logger.info("Manually triggering bill upload job")
        await upload_bills_job()
        return {"message": "Bill upload job completed"}
    except Exception as e:
        logger.error(f"Failed to execute bill upload job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute bill upload job")

@app.post("/trigger-report", tags=["Jobs"])
async def trigger_weekly_report() -> dict[str, str]:
    """Manually trigger the weekly report job
    
    Returns:
        dict: Job completion status message
    
    Raises:
        HTTPException: If the job fails to execute
    """
    try:
        logger.info("Manually triggering weekly report job")
        await send_weekly_report_job()
        return {"message": "Weekly report job completed"}
    except Exception as e:
        logger.error(f"Failed to execute weekly report job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute weekly report job")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")