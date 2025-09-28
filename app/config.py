import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Desafio Python Alpha"
    app_description: str = "Planilha Web App com Atualização em Tempo Real"
    debug: bool = False
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    sheet_url: str = "https://docs.google.com/spreadsheets/d/1OO7gDKXv4YJiDfpfrIHaXIa_XUgDhl3rG2FQImQ-ixY/export?format=csv&gid=0"
    
    update_interval_seconds: int = 30
    
    max_connections: int = 100
    
    request_timeout: int = 10
    max_retries: int = 3
    
    log_level: str = "INFO"
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('port must be between 1 and 65535')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings