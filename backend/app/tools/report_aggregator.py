from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json

@dataclass
class Recommendation:
    category: str
    text: str
    impact: str # High, Medium, Low

@dataclass
class SiteReport:
    overall_score: int
    module_scores: Dict[str, int]
    recommendations: List[Recommendation]
    summary: str

def aggregate_report(module_results: List[Any]) -> SiteReport:
    """
    Aggregates results from various modules into a single report.
    Expects module_results to be a list of SQLAlchemy ModuleResult objects or dicts.
    """
    
    scores = {
        "security": 0,
        "seo": 0,
        "performance": 0,
        "accessibility": 0
    }
    
    recommendations = []
    
    # Helper to safe get from result_json
    def get_result(mr):
        if hasattr(mr, 'result_json'):
            return mr.result_json
        return mr.get('result_json', {})

    def get_name(mr):
        if hasattr(mr, 'module_name'):
            return mr.module_name
        return mr.get('module_name', '')

    # 1. Extract scores and issues
    for mr in module_results:
        name = get_name(mr)
        data = get_result(mr)
        
        if not data:
            continue
            
        if name == "security_hygiene":
            scores["security"] += data.get("score", 0) * 0.5 # 50% of security score
            for rec in data.get("recommendations", []):
                recommendations.append(Recommendation("Security", rec, "High"))
                
        elif name == "zap_security":
            # ZAP doesn't return a simple score, but we can deduct based on issues
            issues = data.get("issues", [])
            zap_score = 100
            for issue in issues:
                risk = issue.get("risk", "Low")
                if risk == "High": zap_score -= 20
                elif risk == "Medium": zap_score -= 10
                else: zap_score -= 2
            scores["security"] += max(0, zap_score) * 0.5 # 50% of security score
            
            for issue in issues:
                recommendations.append(Recommendation("Security", f"{issue.get('name')}: {issue.get('solution')}", issue.get("risk", "Low")))

        elif name == "analytics_seo":
            scores["seo"] = data.get("score", 0)
            for rec in data.get("recommendations", []):
                recommendations.append(Recommendation("SEO", rec, "Medium"))

        elif name == "accessibility":
            scores["accessibility"] = data.get("score", 0)
            # Accessibility violations are complex, just adding generic rec for now
            if data.get("violations"):
                recommendations.append(Recommendation("Accessibility", f"Fix {len(data.get('violations'))} accessibility violations", "High"))

        elif name == "lighthouse":
            l_scores = data.get("scores", {})
            scores["performance"] = int(l_scores.get("performance", 0) * 100)
            # Lighthouse also has seo and accessibility, we could average them or just use specific modules
            # For now, let's trust our specific modules more, but mix if needed.
            # Actually, let's just use Lighthouse performance for performance.
            
            for rec in data.get("recommendations", []):
                recommendations.append(Recommendation("Performance", rec, "Medium"))

    # 2. Calculate Overall Score
    # Weights: Security 30%, SEO 30%, Perf 20%, Accessibility 20%
    overall = (
        scores["security"] * 0.3 +
        scores["seo"] * 0.3 +
        scores["performance"] * 0.2 +
        scores["accessibility"] * 0.2
    )
    
    return SiteReport(
        overall_score=int(overall),
        module_scores=scores,
        recommendations=recommendations[:10], # Top 10
        summary=f"Overall site score is {int(overall)}/100."
    )
