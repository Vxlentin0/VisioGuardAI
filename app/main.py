from fastapi import FastAPI
from app.routes.detection import router as detection_router

app = FastAPI(title="VisioGuardAI")

app.include_router(detection_router, prefix="/api/detect")