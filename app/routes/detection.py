from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.services.detector import detect_objects
from app.services.captioner import generate_caption
from app.security.auth import validate_api_key
from app.security.rate_limit import rate_limiter
from starlette.status import HTTP_400_BAD_REQUEST

router = APIRouter()

@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    api_key: str = Depends(validate_api_key)
):
    await rate_limiter.check(api_key)

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="File uploaded is not an image"
        )

    try:
        image_bytes = await file.read()
        boxes = detect_objects(image_bytes)
        caption = generate_caption(image_bytes)
        return {
            "detections": boxes,
            "caption": caption
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )