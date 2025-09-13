from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import select
import json

from app.db import get_session
from app.models import Disease, DiseaseDetection
from app.services.storage import get_storage_provider
from app.services.ml_model import classify_image
from app.services.ai_text import generate_text
from app.schemas import TextAnalysisRequest

router = APIRouter(prefix="/disease", tags=["Disease AI"])

@router.post("/detect")
async def detect_disease(image: UploadFile = File(...), session=Depends(get_session)):
    storage = get_storage_provider()
    image_url = storage.save_file(image)

    preds = classify_image(image_url, domain="disease", top_k=5)
    top = preds[0]
    label = top["label"]
    score = float(top["score"])

    # find or create disease
    q = session.exec(select(Disease).where(Disease.name.ilike(label)))
    disease = q.first()
    if not disease:
        desc = generate_text(f"Write a short description (3 lines) for plant disease '{label}', signs on leaves/fruit and suggested quick actions.")
        disease = Disease(name=label, description=desc, image_url=image_url)
        session.add(disease)
        session.commit()
        session.refresh(disease)

    det = DiseaseDetection(disease_id=disease.id, disease_name=label, confidence=score, image_url=image_url, raw_result=json.dumps(preds))
    session.add(det)
    session.commit()
    session.refresh(det)

    return {"id": det.id, "disease_id": disease.id, "name": label, "confidence": score, "image_url": image_url, "raw_result": preds}

@router.post("/analyze")
def analyze_symptoms(req: TextAnalysisRequest):
    prompt = f"Farmer reports: {req.description}. Identify likely plant diseases or pests (top 3), explain why, and give step-by-step immediate actions and recommended followups."
    result = generate_text(prompt)
    return {"input": req.description, "analysis": result}
