import os, json, requests
from PIL import Image
from io import BytesIO

# CLIP imports
import torch
from transformers import CLIPProcessor, CLIPModel, pipeline

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Load CLIP (for zero-shot)
CLIP_MODEL = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")
_clip_ready = False
try:
    clip_model = CLIPModel.from_pretrained(CLIP_MODEL)
    clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model.to(device)
    _clip_ready = True
except Exception:
    clip_model = None
    clip_processor = None
    _clip_ready = False

# Generic ImageNet fallback classifier (ViT)
VIT_NAME = os.getenv("HF_VIT_NAME", "google/vit-base-patch16-224")
vit_classifier = pipeline("image-classification", model=VIT_NAME)

# Hugging Face Inference API helper (for disease model)
HF_API_KEY = os.getenv("HF_API_KEY")
def hf_image_inference(model: str, image_url: str):
    if not HF_API_KEY:
        raise RuntimeError("HF_API_KEY missing")
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    with requests.get(image_url, stream=True, timeout=30) as resp:
        img_bytes = resp.content
    r = requests.post(url, headers=headers, data=img_bytes, timeout=60)
    return r.json()

def _load_labels(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _load_image_bytes(url):
    r = requests.get(url, timeout=15)
    return Image.open(BytesIO(r.content)).convert("RGB")

# Attempt to use local YOLO (ultralytics) if explicitly enabled AND installed
ENABLE_LOCAL_YOLO = os.getenv("ENABLE_LOCAL_YOLO", "false").lower() in ("1","true","yes")
YOLO_AVAILABLE = False
if ENABLE_LOCAL_YOLO:
    try:
        from ultralytics import YOLO
        YOLO_AVAILABLE = True
    except ImportError:
        YOLO_AVAILABLE = False


def classify_image(image_url: str, domain: str = "pest", top_k: int = 3):
    """
    domain: 'pest' | 'disease' | 'generic'
    Returns: list of dicts {"label":..., "score":...}
    """

    # 1) If domain == 'pest' and local YOLO enabled & available
    if domain == "pest" and YOLO_AVAILABLE:
        weights = os.getenv("YOLO_WEIGHTS_PATH", "./models/yolo11s-pest-detection.pt")
        if os.path.exists(weights):
            model = YOLO(weights)
            results = model.predict(source=image_url, imgsz=640, conf=0.2)
            out = []
            for r in results:
                for box in r.boxes:
                    label = r.names[int(box.cls.cpu().numpy())]
                    conf = float(box.conf.cpu().numpy())
                    out.append({"label": label, "score": conf})
            out = sorted(out, key=lambda x: x["score"], reverse=True)
            return out[:top_k]
        # else: fallthrough

    # 2) If domain == 'disease' and HF model available, call HF inference model
    if domain == "disease" and HF_API_KEY:
        hf_model = os.getenv(
            "HF_DISEASE_MODEL",
            "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification",
        )
        try:
            resp = hf_image_inference(hf_model, image_url)
            if isinstance(resp, list):
                return resp[:top_k]
        except Exception:
            pass

    # 3) CLIP zero-shot if labels exist and CLIP is ready
    labels_path = os.path.join(DATA_DIR, f"{domain}_labels.json")
    if os.path.exists(labels_path) and _clip_ready:
        candidate_labels = _load_labels(labels_path)
        img = _load_image_bytes(image_url)
        inputs = clip_processor(
            text=candidate_labels, images=img, return_tensors="pt", padding=True
        ).to(clip_model.device)
        with torch.no_grad():
            image_embeds = clip_model.get_image_features(pixel_values=inputs["pixel_values"])
            text_embeds = clip_model.get_text_features(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
            )
        image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
        sims = (text_embeds @ image_embeds.T).squeeze(1)
        probs = torch.softmax(sims, dim=0).cpu().tolist()
        pairs = sorted(zip(candidate_labels, probs), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"label": l, "score": float(s)} for l, s in pairs]

    # 4) fallback to generic vit classifier
    return vit_classifier(image_url, top_k=top_k)
