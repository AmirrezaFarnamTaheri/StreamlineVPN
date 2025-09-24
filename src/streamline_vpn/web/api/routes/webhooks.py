from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

webhooks_router = APIRouter()

class Webhook(BaseModel):
    url: str
    event: str

webhooks: List[Webhook] = []

@webhooks_router.post("/webhooks")
async def create_webhook(webhook: Webhook):
    """Create a new webhook."""
    webhooks.append(webhook)
    return {"message": "Webhook created successfully"}

@webhooks_router.get("/webhooks")
async def get_webhooks():
    """Get all registered webhooks."""
    return webhooks

@webhooks_router.delete("/webhooks")
async def delete_webhook(webhook: Webhook):
    """Delete a webhook."""
    try:
        webhooks.remove(webhook)
        return {"message": "Webhook deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Webhook not found")
