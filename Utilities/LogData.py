class LogData:
    def __init__(
        self,
        pathToFile : str = "logs.logdata.log",
        level : str = "DEBUG",
        rotation : str = "10 MB",
        retention : str = "1 week",
        format : str = "{time} | {level} | {message}"):
        self.PathToFile = pathToFile
        self.Level = level
        self.Rotation = rotation
        self.Retention = retention
        self.Format = format