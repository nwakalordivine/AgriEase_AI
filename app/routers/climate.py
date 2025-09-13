from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
import os, requests, json

from app.db import get_session
from app.models import ClimateData
from app.services.ai_text import generate_text

router = APIRouter(prefix="/climate", tags=["Climate AI"])

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

@router.get("/forecast/{region}")
def forecast(region: str, session=Depends(get_session)):
    if OPENWEATHER_API_KEY:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather", params={"q": region, "appid": OPENWEATHER_API_KEY, "units": "metric"}, timeout=10)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Weather provider error")
        data = r.json()
    else:
        data = {"region": region, "forecast": "No OpenWeather API key; mock sunny data"}

    cd = ClimateData(region=region, forecast_json=json.dumps(data))
    session.add(cd)
    session.commit()
    return data


@router.get("/recommendations/{region}")
def recommendations(region: str, session=Depends(get_session)):
    # 1. Check DB first
    q = session.exec(
        select(ClimateData).where(ClimateData.region == region).order_by(ClimateData.id.desc())
    )
    cd = q.first()

    if cd:
        forecast_text = cd.forecast_json
    else:
        # 2. Call OpenWeather API as fallback
        url = f"http://api.openweathermap.org/data/2.5/weather?q={region}&appid={OPENWEATHER_API_KEY}&units=metric"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            forecast_text = (
                f"Temperature: {data['main']['temp']}°C, "
                f"Humidity: {data['main']['humidity']}%, "
                f"Condition: {data['weather'][0]['description']}"
            )
            # 3. Cache result in DB
            new_entry = ClimateData(region=region, forecast_json=forecast_text)
            session.add(new_entry)
            session.commit()
        else:
            forecast_text = "No forecast data."

    # 4. Generate advice
    prompt = f"""
    Given the following forecast for {region}: {forecast_text}.
    Provide 5 short, prioritized farming recommendations and any urgent actions for smallholder farmers.
    """
    advice = generate_text(prompt)

    return {"region": region, "forecast": forecast_text, "recommendations":  advice}

