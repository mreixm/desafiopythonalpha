from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class WebSocketMessageType(str, Enum):
    INITIAL_DATA = "initial_data"
    DATA_UPDATE = "data_update"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class SheetRecord(BaseModel):
    data: Dict[str, Any] = Field(..., description="Dados do registro")
    
    @validator('data')
    def validate_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError('data must be a dictionary')
        return v


class SheetData(BaseModel):
    records: List[SheetRecord] = Field(default_factory=list)
    total_records: int = Field(0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('total_records', always=True)
    def validate_total_records(cls, v, values):
        records = values.get('records', [])
        if v != len(records):
            return len(records)
        return v


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    data: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None
    error: Optional[str] = None


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    total_records: int = 0


class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"