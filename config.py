from loguru import logger

logger.add("logs/Logs.txt", rotation="1 day", level="INFO")