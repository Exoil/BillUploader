from loguru import logger
from Utilities.LogData import LogData
import sys

class LogConfig:
    """Class to handle logging configuration."""

    @staticmethod
    def setLogging(
        logData: LogData):
        logger.remove()
        logger.add(
                sink = sys.stdout,
                level = logData.Level,
                format = logData.Format)
        
        logger.add(
            sink = logData.PathToFile,
            rotation = logData.Rotation,
            retention = logData.Retention,
            format = logData.Format
        )
