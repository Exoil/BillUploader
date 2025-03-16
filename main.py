from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from Utilities.LogConfiguration import LogConfig
from Utilities.LogData import LogData
from loguru import logger


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
async def version():
    return {"version": "1.0.0"}

app.add_api_route("/", version, methods=["GET"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")