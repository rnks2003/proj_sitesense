import requests
import time
from dataclasses import dataclass
from typing import List, Dict, Any
from ..config import settings

@dataclass
class ZapIssue:
    risk: str
    confidence: str
    name: str
    description: str
    url: str
    solution: str

@dataclass
class ZapResult:
    issues: List[ZapIssue]
    status: str # "completed", "failed", "skipped"

def run_zap_scan(url: str, scan_id: str) -> ZapResult:
    base_url = f"http://{settings.ZAP_HOST}:{settings.ZAP_PORT}"
    headers = {"X-ZAP-API-Key": settings.ZAP_API_KEY}
    
    # 1. Check if ZAP is running
    try:
        resp = requests.get(f"{base_url}/JSON/core/view/version/", headers=headers, timeout=2)
        if resp.status_code != 200:
            print("ZAP is not running or reachable.")
            return ZapResult(issues=[], status="skipped")
    except requests.exceptions.ConnectionError:
        print("ZAP is not running (connection error).")
        return ZapResult(issues=[], status="skipped")
    except Exception as e:
        print(f"Error checking ZAP status: {e}")
        return ZapResult(issues=[], status="failed")

    print(f"ZAP is running. Starting scan for {url}...")

    # 2. Trigger Spider
    try:
        # Start spider
        resp = requests.get(
            f"{base_url}/JSON/spider/action/scan/",
            params={"url": url},
            headers=headers
        )
        scan_id_zap = resp.json().get("scan")
        if not scan_id_zap:
             print("Failed to start ZAP spider.")
             return ZapResult(issues=[], status="failed")
             
        # Poll for spider completion
        while True:
            resp = requests.get(
                f"{base_url}/JSON/spider/view/status/",
                params={"scanId": scan_id_zap},
                headers=headers
            )
            status = int(resp.json().get("status", 0))
            if status >= 100:
                break
            time.sleep(1)
            
        print("ZAP Spider completed.")
        
        # 3. Active Scan (Optional - skipping for now to keep it fast/safe, or make it configurable)
        # To enable: /JSON/ascan/action/scan/
        
        # 4. Fetch Alerts
        resp = requests.get(
            f"{base_url}/JSON/core/view/alerts/",
            params={"baseurl": url},
            headers=headers
        )
        alerts = resp.json().get("alerts", [])
        
        issues = []
        for alert in alerts:
            issues.append(ZapIssue(
                risk=alert.get("risk"),
                confidence=alert.get("confidence"),
                name=alert.get("alert"),
                description=alert.get("description"),
                url=alert.get("url"),
                solution=alert.get("solution")
            ))
            
        return ZapResult(issues=issues, status="completed")
        
    except Exception as e:
        print(f"Error running ZAP scan: {e}")
        return ZapResult(issues=[], status="failed")
