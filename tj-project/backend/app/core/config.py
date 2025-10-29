from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    #DATABASE_URL: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        password = quote_plus(self.DB_PASS)
        return f"postgresql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

settings = Settings()