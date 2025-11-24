import subprocess
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PerformanceResult:
    scores: Dict[str, float]
    core_web_vitals: Dict[str, Any]
    recommendations: List[str]
    full_report: Dict[str, Any]

def run_lighthouse(url: str, scan_id: str) -> PerformanceResult:
    # Use absolute path for data directory
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
    output_dir = os.path.join(base_dir, "lighthouse")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{scan_id}.json")
    
    # Set CHROME_PATH for lighthouse to find the browser
    env = os.environ.copy()
    from ..config import settings
    env["CHROME_PATH"] = settings.CHROME_PATH
    
    # Check if lighthouse is installed
    import shutil
    if not shutil.which("lighthouse"):
        print("Lighthouse CLI not found in PATH")
        raise FileNotFoundError("Lighthouse CLI not found. Please install it with 'npm install -g lighthouse'")

    cmd = [
        "lighthouse",
        url,
        "--quiet",
        "--chrome-flags=--headless",
        "--output=json",
        f"--output-path={output_path}"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, env=env)
        
        with open(output_path, 'r') as f:
            lhr = json.load(f)
            
        # Clean up
        try:
            os.remove(output_path)
            # Try to remove dir if empty
            os.rmdir(output_dir)
        except:
            pass
            
        scores = {
            "performance": lhr["categories"]["performance"]["score"],
            "accessibility": lhr["categories"]["accessibility"]["score"],
            "best-practices": lhr["categories"]["best-practices"]["score"],
            "seo": lhr["categories"]["seo"]["score"],
        }
        
        audits = lhr["audits"]
        core_web_vitals = {
            "FCP": audits.get("first-contentful-paint", {}).get("displayValue"),
            "LCP": audits.get("largest-contentful-paint", {}).get("displayValue"),
            "TBT": audits.get("total-blocking-time", {}).get("displayValue"),
            "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue"),
            "SI": audits.get("speed-index", {}).get("displayValue"),
        }
        
        recommendations = []
        # Extract some high-impact recommendations (audits with score < 1 and high weight)
        # For simplicity, just taking a few failed audits
        for audit_id, audit in audits.items():
            if audit.get("score") is not None and audit.get("score") < 0.9:
                if audit.get("details", {}).get("type") == "opportunity":
                     recommendations.append(audit.get("title"))
                     
        return PerformanceResult(
            scores=scores,
            core_web_vitals=core_web_vitals,
            recommendations=recommendations[:5], # Limit to 5
            full_report=lhr
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Lighthouse failed: {e}")
        raise e
    except Exception as e:
        print(f"Error parsing lighthouse output: {e}")
        raise e
