from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Pest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PestMethod(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pest_id: int = Field(foreign_key="pest.id")
    method_type: str
    description: str

class PestDetection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pest_id: Optional[int] = Field(default=None, foreign_key="pest.id")
    pest_name: str
    confidence: float
    image_url: str
    raw_result: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Disease(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DiseaseDetection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    disease_id: Optional[int] = Field(default=None, foreign_key="disease.id")
    disease_name: str
    confidence: float
    image_url: str
    raw_result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClimateData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    region: str
    forecast_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
