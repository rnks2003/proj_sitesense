from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .. import models, schemas
from ..db import get_db

router = APIRouter(
    prefix="/scan",
    tags=["scans"],
)

@router.get("/")
async def list_scans(db: Session = Depends(get_db)):
    """List all scans ordered by most recent first"""
    scans = db.query(models.Scan).order_by(models.Scan.created_at.desc()).limit(50).all()
    return scans

from ..services import scan_service
import asyncio

def run_scan_sync(scan_id: str, url: str):
    """Wrapper to run async scan in background task"""
    asyncio.run(scan_service.run_full_scan(scan_id, url))

@router.post("/", response_model=schemas.ScanRead)
def create_scan(scan: schemas.ScanCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_scan = models.Scan(url=scan.url, status="queued")
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    background_tasks.add_task(run_scan_sync, db_scan.id, db_scan.url)
    
    return db_scan


@router.get("/{scan_id}", response_model=schemas.ScanRead)
def read_scan(scan_id: str, db: Session = Depends(get_db)):
    db_scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return db_scan

@router.delete("/{scan_id}")
def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    """Delete a single scan and its related data"""
    try:
        db_scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if db_scan is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Delete the scan (cascade will handle module_results and files)
        db.delete(db_scan)
        db.commit()
        return {"message": f"Scan {scan_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete scan: {str(e)}")

@router.delete("/clear")
def clear_all_scans(db: Session = Depends(get_db)):
    """Clear all scans and their results from the database"""
    try:
        # Delete all module results first (foreign key constraint)
        db.query(models.ModuleResult).delete()
        # Delete all files
        db.query(models.File).delete()
        # Delete all scans
        db.query(models.Scan).delete()
        db.commit()
        return {"message": "All scans cleared successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear scans: {str(e)}")
