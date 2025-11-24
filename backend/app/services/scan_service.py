from sqlalchemy.orm import Session
from .. import models, workflow
from ..db import SessionLocal
import json
from dataclasses import asdict
import asyncio

async def run_full_scan(scan_id: str, url: str):
    """
    Executes the full scan pipeline.
    """
    print(f"Starting scan {scan_id} for {url}")
    
    # Create a new session for the background task
    db = SessionLocal()
    
    try:
        # Initialize state
        initial_state = {
            "scan_id": scan_id,
            "url": url,
            "artifact": None,
            "results": []
        }
        
        print(f"Starting LangGraph workflow for {url}...")
        # Invoke graph
        final_state = await workflow.app.ainvoke(initial_state)
        
        # Save results
        print("Workflow completed. Saving results...")
        for res in final_state['results']:
            # Save module result
            db.add(models.ModuleResult(
                scan_id=scan_id,
                module_name=res['module_name'],
                status=res['status'],
                result_json=res['result_json']
            ))
        
        # Update scan status
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan:
            scan.status = "completed"
            db.commit()
            print(f"Scan {scan_id} completed")
            
    except Exception as e:
        print(f"Error running scan {scan_id}: {e}")
        import traceback
        traceback.print_exc()
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            scan.error_message = str(e)
            db.commit()
    finally:
        db.close()
