from dataclasses import dataclass
from typing import List
from .page_renderer import PageArtifact
import re

@dataclass
class SecurityHygieneResult:
    score: int
    findings: List[str]
    recommendations: List[str]

def analyze_security_hygiene(artifact: PageArtifact) -> SecurityHygieneResult:
    findings = []
    recommendations = []
    score = 100

    # 1. HTTPS check (using artifact.url if available, or just assuming from headers/logic)
    # Since we don't have the original URL in artifact, we might miss this if we don't pass it.
    # But we can check if the screenshot path or something indicates it, or just rely on headers.
    # Actually, let's assume the caller passes the URL or we look at network logs.
    # For now, we'll skip strict URL check unless we add it to PageArtifact.
    # Let's check Strict-Transport-Security header.
    
    headers = {k.lower(): v for k, v in artifact.headers.items()}
    
    if 'strict-transport-security' not in headers:
        score -= 10
        findings.append("Missing Strict-Transport-Security header")
        recommendations.append("Enable HSTS to prevent man-in-the-middle attacks.")

    if 'content-security-policy' not in headers:
        score -= 10
        findings.append("Missing Content-Security-Policy header")
        recommendations.append("Configure CSP to mitigate XSS and data injection attacks.")
        
    if 'x-frame-options' not in headers:
        score -= 10
        findings.append("Missing X-Frame-Options header")
        recommendations.append("Set X-Frame-Options to DENY or SAMEORIGIN to prevent clickjacking.")
        
    if 'x-content-type-options' not in headers:
        score -= 5
        findings.append("Missing X-Content-Type-Options header")
        recommendations.append("Set X-Content-Type-Options to nosniff.")

    # Cookie checks
    for cookie in artifact.cookies:
        if not cookie.get('secure'):
            score -= 5
            findings.append(f"Cookie '{cookie['name']}' is not Secure")
            recommendations.append(f"Set the Secure flag for cookie '{cookie['name']}'.")
        if not cookie.get('httpOnly'):
            score -= 5
            findings.append(f"Cookie '{cookie['name']}' is not HttpOnly")
            recommendations.append(f"Set the HttpOnly flag for cookie '{cookie['name']}'.")
            
    # JS Libs (simple regex on DOM)
    # This is a basic check
    if 'jquery' in artifact.dom_html.lower():
        findings.append("jQuery detected")
    if 'react' in artifact.dom_html.lower():
        findings.append("React detected")

    return SecurityHygieneResult(
        score=max(0, score),
        findings=findings,
        recommendations=list(set(recommendations))
    )
