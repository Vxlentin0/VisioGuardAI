from fastapi import APIRouter, File, UploadFile
from app.services.detector import detect_objects
from app.services.captioner import generate_caption

router = APIRouter()

@router.post("/image")
async def detect_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    boxes = detect_objects(image_bytes)
    caption = generate_caption(image_bytes)
    return {
        "detections": boxes,
        "caption": caption
    }