from dataclasses import dataclass
from typing import List
from .page_renderer import PageArtifact
from bs4 import BeautifulSoup

@dataclass
class AnalyticsSEOResult:
    score: int
    analytics_tools: List[str]
    seo_issues: List[str]
    recommendations: List[str]

def analyze_analytics_seo(artifact: PageArtifact) -> AnalyticsSEOResult:
    soup = BeautifulSoup(artifact.dom_html, 'html.parser')
    score = 100
    analytics_tools = []
    seo_issues = []
    recommendations = []

    # Title
    title = soup.find('title')
    if not title or not title.string:
        score -= 20
        seo_issues.append("Missing <title> tag")
        recommendations.append("Add a descriptive <title> tag.")
    elif len(title.string) < 10:
        score -= 5
        seo_issues.append("Title tag is too short")
        recommendations.append("Make the title tag more descriptive.")

    # Meta Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content'):
        score -= 20
        seo_issues.append("Missing meta description")
        recommendations.append("Add a meta description to improve search visibility.")

    # H1
    h1s = soup.find_all('h1')
    if not h1s:
        score -= 10
        seo_issues.append("Missing <h1> tag")
        recommendations.append("Use at least one <h1> tag for the main heading.")
    elif len(h1s) > 1:
        score -= 5
        seo_issues.append("Multiple <h1> tags found")
        recommendations.append("Use only one <h1> tag per page.")

    # Analytics detection (simple string matching in scripts)
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            content = script.string.lower()
            if 'google-analytics.com' in content or 'gtag' in content:
                analytics_tools.append("Google Analytics")
            if 'googletagmanager.com' in content:
                analytics_tools.append("Google Tag Manager")
            if 'facebook.net' in content or 'fbq(' in content:
                analytics_tools.append("Meta Pixel")

    analytics_tools = list(set(analytics_tools))
    if not analytics_tools:
        recommendations.append("Consider adding analytics tools like Google Analytics.")

    return AnalyticsSEOResult(
        score=max(0, score),
        analytics_tools=analytics_tools,
        seo_issues=seo_issues,
        recommendations=recommendations
    )
