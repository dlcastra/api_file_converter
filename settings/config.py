from decouple import config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY", "mock-secret-key")

    AWS_ACCESS_KEY_ID: str = config("AWS_ACCESS_KEY_ID", "mock-access-key")
    AWS_SECRET_ACCESS_KEY: str = config("AWS_SECRET_ACCESS_KEY", "mock-secret-key")
    AWS_S3_BUCKET_NAME: str = config("AWS_S3_BUCKET_NAME", "mock-bucket")
    AWS_S3_REGION: str = config("AWS_S3_REGION", "us-east-1")


settings = Settings()
