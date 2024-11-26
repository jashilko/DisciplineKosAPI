import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str

    model_config = SettingsConfigDict(
        env_file='env.env'
    )


settings = Settings()


# def get_db_url():
#     return (
#         f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
#         f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
#     )

def get_db_url():
    return (
        'postgresql+psycopg2://{}:{}@{}/{}'.
        format(settings.DB_USER,
               settings.DB_PASSWORD,
               settings.DB_HOST,
               settings.DB_NAME)
    )


def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}
