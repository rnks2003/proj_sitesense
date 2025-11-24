from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..schemas import ChatRequest, ChatResponse
from ..services.chat_service import chat_with_gemini
from ..db import get_db

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Gemini about a specific scan.
    The scan context is provided directly in the request body.
    """
    if not request.api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is required")

    # We don't need to fetch scan from DB anymore, context is in request
    scan_context = request.scan_context or {}
    
    response_text = await chat_with_gemini(
        message=request.message,
        history=request.history,
        api_key=request.api_key,
        scan_context=scan_context
    )
    
    return ChatResponse(response=response_text, status="success")
