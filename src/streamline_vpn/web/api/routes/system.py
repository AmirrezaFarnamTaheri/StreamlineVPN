from fastapi import APIRouter
from datetime import datetime

router = APIRouter()
start_time = datetime.now()

@router.get("/health")
async def health():
    uptime = (datetime.now() - start_time).total_seconds()
    return {"status": "healthy", "uptime": uptime, "version": "2.0.0"}

@router.get("/")
async def root():
    return {"message": "StreamlineVPN API", "version": "2.0.0"}