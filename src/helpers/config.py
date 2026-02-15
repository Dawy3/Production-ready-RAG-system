from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    APP_NAME: str 
    APP_VERSION: str
    OPENAI_API_KEY: str
    
    MONOGDB_URL: str
    MONOGDB_DATABASE: str
    
    class Config:
        env_file = ".env"
        


def get_settigns():
    return Settings()


settings = get_settigns()