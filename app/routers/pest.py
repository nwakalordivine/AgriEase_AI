from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import select
import json

from app.db import get_session
from app.models import Pest, PestMethod, PestDetection
from app.services.storage import get_storage_provider
from app.services.ml_model import classify_image
from app.services.ai_text import generate_text

router = APIRouter(prefix="/pest", tags=["Pest AI"])

@router.post("/detect")
async def detect_pest(image: UploadFile = File(...), session=Depends(get_session)):
    storage = get_storage_provider()
    image_url = storage.save_file(image)

    preds = classify_image(image_url, domain="pest", top_k=5)
    top = preds[0]
    label = top["label"]
    score = float(top["score"])

    # find or create pest
    q = session.exec(select(Pest).where(Pest.name.ilike(label)))
    pest = q.first()
    if not pest:
        desc = generate_text(f"Write a short description (3 lines) of the agricultural pest '{label}', common crops affected, and visible signs on plants.")
        pest = Pest(name=label, description=desc, image_url=image_url)
        session.add(pest)
        session.commit()
        session.refresh(pest)
        # generate methods
        methods_text = generate_text(f"List preventive methods and corrective actions for '{label}'. Provide short actionable steps for smallholder farmers.")
        pm = PestMethod(pest_id=pest.id, method_type="general", description=methods_text)
        session.add(pm)
        session.commit()

    det = PestDetection(pest_id=pest.id, pest_name=label, confidence=score, image_url=image_url, raw_result=json.dumps(preds))
    session.add(det)
    session.commit()
    session.refresh(det)

    return {"id": det.id, "pest_id": pest.id, "name": label, "confidence": score, "image_url": image_url, "raw_result": preds}

@router.get("/{pest_id}")
def get_pest(pest_id: int, session=Depends(get_session)):
    pest = session.get(Pest, pest_id)
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    methods = session.exec(select(PestMethod).where(PestMethod.pest_id == pest.id)).all()
    return {"id": pest.id, "name": pest.name, "description": pest.description, "image_url": pest.image_url,
            "methods": [{"id": m.id, "type": m.method_type, "description": m.description} for m in methods]}

@router.get("/methods/{pest_name}")
def get_pest_methods(pest_name: str, session=Depends(get_session)):
    q = session.exec(select(Pest).where(Pest.name.ilike(pest_name)))
    pest = q.first()
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    methods = session.exec(select(PestMethod).where(PestMethod.pest_id == pest.id)).all()
    if not methods:
        methods_text = generate_text(f"Provide preventive and corrective methods for '{pest.name}' for small farmers in bullet points.")
        pm = PestMethod(pest_id=pest.id, method_type="general", description=methods_text)
        session.add(pm)
        session.commit()
        methods = [pm]
    return {"pest": pest.name, "methods": [{"type": m.method_type, "description": m.description} for m in methods]}
