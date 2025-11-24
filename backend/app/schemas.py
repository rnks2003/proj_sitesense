from pydantic import BaseModel, HttpUrl, model_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime

class ScanBase(BaseModel):
    url: str

class ScanCreate(ScanBase):
    pass

class ModuleResultRead(BaseModel):
    id: int
    module_name: str
    status: str
    result_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    @model_serializer(mode='wrap')
    def ser_model(self, serializer):
        data = serializer(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'] + 'Z' if not data['created_at'].endswith('Z') else data['created_at']
        return data

    class Config:
        from_attributes = True

class ScanRead(ScanBase):
    id: str
    normalized_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    module_results: List[ModuleResultRead] = []

    @model_serializer(mode='wrap')
    def ser_model(self, serializer):
        data = serializer(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'] + 'Z' if not data['created_at'].endswith('Z') else data['created_at']
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'] + 'Z' if not data['updated_at'].endswith('Z') else data['updated_at']
        return data

    class Config:
        from_attributes = True

class ScanStatus(BaseModel):
    id: str
    status: str
