from sqlalchemy.orm import Session
from .. import models
from ..db import SessionLocal

def save_file(scan_id: str, file_type: str, data: bytes, content_type: str):
    """
    Saves a file to the database.
    """
    db = SessionLocal()
    try:
        # Check if file already exists, update if so
        existing = db.query(models.File).filter(
            models.File.scan_id == scan_id,
            models.File.file_type == file_type
        ).first()
        
        if existing:
            existing.data = data
            existing.content_type = content_type
        else:
            new_file = models.File(
                scan_id=scan_id,
                file_type=file_type,
                data=data,
                content_type=content_type
            )
            db.add(new_file)
        
        db.commit()
    except Exception as e:
        print(f"Error saving file {file_type} for scan {scan_id}: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def get_file_url(scan_id: str, file_type: str) -> str:
    """
    Returns the URL for a file.
    """
    # Assuming the API is served at /api/v1 or similar, but here we just return the relative path
    # The frontend should handle the base URL or we can hardcode it if we know it.
    # Based on files.py, the route is /files/{scan_id}/{file_type}
    return f"/files/{scan_id}/{file_type}"
