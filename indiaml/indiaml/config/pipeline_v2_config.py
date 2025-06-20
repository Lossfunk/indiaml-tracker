from pydantic_settings import BaseSettings

class Config(BaseSettings):
    OUTPUT_DIRECTORY: str = "./output"
    LOGS_DIRECTORY: str = "./logs"


config = Config()