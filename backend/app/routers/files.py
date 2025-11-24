from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{scan_id}/{file_type}")
async def serve_file(scan_id: str, file_type: str, db: Session = Depends(get_db)):
    """
    Serve files from database.
    file_type can be: screenshot, attention_heatmap, click_heatmap, lighthouse_report
    """
    # Query the file from database
    file_record = db.query(models.File).filter(
        models.File.scan_id == scan_id,
        models.File.file_type == file_type
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return the file data with appropriate content type
    return Response(
        content=file_record.data,
        media_type=file_record.content_type
    )
