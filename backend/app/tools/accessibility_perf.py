from dataclasses import dataclass
from typing import List
from playwright.async_api import async_playwright

@dataclass
class AccessibilityIssue:
    id: str
    impact: str
    description: str
    help_url: str
    nodes: List[str]

@dataclass
class AccessibilityResult:
    score: int
    issues: List[AccessibilityIssue]

async def analyze_accessibility(url: str) -> AccessibilityResult:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        
        # Inject axe-core
        await page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js")
        
        # Run axe
        results = await page.evaluate("async () => await axe.run()")
        
        issues = []
        for violation in results['violations']:
            nodes = [node['target'][0] for node in violation['nodes']]
            issues.append(AccessibilityIssue(
                id=violation['id'],
                impact=violation.get('impact', 'unknown'),
                description=violation['description'],
                help_url=violation['helpUrl'],
                nodes=nodes
            ))
            
        # Calculate a simple score based on violations
        # 100 - (critical * 5 + serious * 3 + moderate * 1)
        score = 100
        for issue in issues:
            if issue.impact == 'critical':
                score -= 5
            elif issue.impact == 'serious':
                score -= 3
            elif issue.impact == 'moderate':
                score -= 1
                
        await browser.close()
        
        return AccessibilityResult(
            score=max(0, score),
            issues=issues
        )
