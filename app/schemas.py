from pydantic import BaseModel
from typing import Optional

class TextAnalysisRequest(BaseModel):
    description: str

class DetectionResponse(BaseModel):
    name: str
    confidence: float
    image_url: str
    raw_result: Optional[dict] = None
