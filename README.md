# Agri AI FastAPI Service

This project provides AI-powered endpoints for agricultural disease, pest, and climate analysis using FastAPI.

## Features
- Disease detection from images
- Pest detection from images
- Climate forecast and farming recommendations
- AI-powered text analysis for symptoms

## Endpoints
See the included Postman collection (`AgriAI_Postman_Collection.json`) for example requests.

## Running Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Set environment variables:**
   - Copy `.env` and fill in required API keys (OpenWeather, Cloudinary, Hugging Face, etc.)
3. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Deploying on Hugging Face Space

1. **Add your API keys to the Space secrets or `.env` file.**
2. **Ensure your Space uses the Docker runtime.**
3. **The provided `Dockerfile` will build and run the FastAPI app.**

## Example Request

```bash
curl -X POST "https://<your-space-url>/disease/detect" -F "image=@path/to/image.jpg"
```

## License
MIT
