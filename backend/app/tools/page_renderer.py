from playwright.async_api import async_playwright, Page
from dataclasses import dataclass
from typing import List, Dict, Any
import os
import json

@dataclass
class PageArtifact:
    screenshot_bytes: bytes
    viewport: dict
    dom_html: str
    headers: dict
    cookies: List[Dict[str, Any]]
    network_logs: List[Dict[str, Any]]
    clickable_elements: List[Dict[str, Any]]

async def render_page(url: str, scan_id: str) -> PageArtifact:
    """
    Renders a page using Playwright, captures a screenshot, and extracts metadata.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        network_logs = []
        
        # Capture network logs
        page.on("request", lambda request: network_logs.append({
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type
        }))

        try:
            response = await page.goto(url, wait_until="networkidle")
            headers = response.headers if response else {}
            
            # Capture screenshot as bytes
            screenshot_bytes = await page.screenshot()
            
            dom_html = await page.content()
            cookies = await context.cookies()
            viewport = page.viewport_size
            
            # Extract clickable elements
            clickable_elements = await page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('a, button, input, [onclick], [role="button"]'));
                    return elements.map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tag: el.tagName,
                            text: el.innerText,
                            href: el.href || null,
                            rect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        };
                    });
                }
            """)
            
            return PageArtifact(
                screenshot_bytes=screenshot_bytes,
                viewport=viewport,
                dom_html=dom_html,
                headers=headers,
                cookies=cookies,
                network_logs=network_logs,
                clickable_elements=clickable_elements
            )
            
        finally:
            await browser.close()
