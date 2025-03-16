from fastapi import FastAPI
from config import logger
import uvicorn
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Handles startup and shutdown events """
    logger.info("🎬 Application starting...")
    yield
    logger.info("🛑 Application shutting down...")

app = FastAPI(lifespan=lifespan)
async def version():
    return {"version": "1.0.0"}

app.add_api_route("/", version, methods=["GET"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")