from typing import TypedDict, List, Optional, Any, Dict
from langgraph.graph import StateGraph, END
from .tools import (
    page_renderer,
    security_hygiene,
    analytics_seo,
    accessibility_perf,
    lighthouse,
    heatmaps,
    security_zap,
    report_aggregator
)
from .models import ModuleResult
from .services.file_service import save_file, get_file_url
from dataclasses import asdict
import asyncio
import json

class ScanState(TypedDict):
    scan_id: str
    url: str
    artifact: Optional[Any] # PageArtifact
    results: List[Dict[str, Any]] # List of ModuleResult dicts (to be saved)

# Nodes
async def render_page_node(state: ScanState):
    print(f"Graph: Rendering page for {state['url']}")
    artifact = await page_renderer.render_page(state['url'], state['scan_id'])
    
    # Save screenshot to DB
    if artifact.screenshot_bytes:
        await asyncio.to_thread(save_file, state['scan_id'], "screenshot", artifact.screenshot_bytes, "image/png")
        
    return {"artifact": artifact}

async def analyze_security_node(state: ScanState):
    print("Graph: Analyzing Security Hygiene")
    result = security_hygiene.analyze_security_hygiene(state['artifact'])
    return {"results": [
        {
            "module_name": "security_hygiene",
            "status": "completed",
            "result_json": asdict(result)
        }
    ]}

async def analyze_seo_node(state: ScanState):
    print("Graph: Analyzing SEO")
    result = analytics_seo.analyze_analytics_seo(state['artifact'])
    return {"results": [
        {
            "module_name": "analytics_seo",
            "status": "completed",
            "result_json": asdict(result)
        }
    ]}

async def analyze_accessibility_node(state: ScanState):
    print("Graph: Analyzing Accessibility")
    result = await accessibility_perf.analyze_accessibility(state['url'])
    return {"results": [
        {
            "module_name": "accessibility",
            "status": "completed",
            "result_json": asdict(result)
        }
    ]}

async def analyze_performance_node(state: ScanState):
    print("Graph: Analyzing Performance (Lighthouse)")
    # Run in thread as it uses subprocess
    result = await asyncio.to_thread(lighthouse.run_lighthouse, state['url'], state['scan_id'])
    return {"results": [
        {
            "module_name": "lighthouse",
            "status": "completed",
            "result_json": asdict(result)
        }
    ]}

async def analyze_heatmaps_node(state: ScanState):
    print("Graph: Analyzing Heatmaps")
    # Run in thread as it uses opencv
    result = await asyncio.to_thread(
        heatmaps.generate_heatmaps, 
        state['artifact'].screenshot_bytes, 
        state['artifact'].clickable_elements, 
        state['scan_id']
    )
    return {"results": [
        {
            "module_name": "heatmaps",
            "status": "completed",
            "result_json": asdict(result)
        }
    ]}

async def analyze_zap_node(state: ScanState):
    print("Graph: Analyzing ZAP Security")
    # Run in thread as it uses requests blocking
    result = await asyncio.to_thread(security_zap.run_zap_scan, state['url'], state['scan_id'])
    return {"results": [
        {
            "module_name": "zap_security",
            "status": result.status,
            "result_json": asdict(result)
        }
    ]}

async def aggregate_report_node(state: ScanState):
    print("Graph: Aggregating Report")
    # Convert dicts back to objects or just pass dicts if aggregator supports it
    # Our aggregator expects objects or dicts, so dicts are fine.
    # state['results'] contains all results accumulated so far
    aggregated_report = report_aggregator.aggregate_report(state['results'])
    
    # IMPORTANT: Append the aggregated report to existing results, don't replace them
    # This preserves individual module results like heatmaps for frontend display
    new_results = state['results'].copy()
    new_results.append({
        "module_name": "aggregated_report",
        "status": "completed",
        "result_json": asdict(aggregated_report)
    })
    
    return {"results": new_results}

# Graph Definition
workflow = StateGraph(ScanState)

workflow.add_node("render_page", render_page_node)
workflow.add_node("analyze_security", analyze_security_node)
workflow.add_node("analyze_seo", analyze_seo_node)
workflow.add_node("analyze_accessibility", analyze_accessibility_node)
workflow.add_node("analyze_performance", analyze_performance_node)
workflow.add_node("analyze_heatmaps", analyze_heatmaps_node)
workflow.add_node("analyze_zap", analyze_zap_node)
workflow.add_node("aggregate_report", aggregate_report_node)

workflow.set_entry_point("render_page")

# Parallel execution after render
workflow.add_edge("render_page", "analyze_security")
workflow.add_edge("render_page", "analyze_seo")
workflow.add_edge("render_page", "analyze_accessibility")
workflow.add_edge("render_page", "analyze_performance")
workflow.add_edge("render_page", "analyze_heatmaps")
workflow.add_edge("render_page", "analyze_zap")

async def analyze_parallel_node(state: ScanState):
    print("Graph: Running parallel analysis")
    
    # Helper function to safely run a module
    async def safe_run(module_name, func):
        try:
            return await func
        except Exception as e:
            print(f"Error in {module_name}: {e}")
            return {"error": str(e), "status": "failed"}
    
    # 1. Security
    f1 = safe_run("security_hygiene", asyncio.to_thread(lambda: security_hygiene.analyze_security_hygiene(state['artifact'])))
    
    # 2. SEO
    f2 = safe_run("analytics_seo", asyncio.to_thread(lambda: analytics_seo.analyze_analytics_seo(state['artifact'])))
    
    # 3. Accessibility
    f3 = safe_run("accessibility", accessibility_perf.analyze_accessibility(state['url']))
    
    # 4. Lighthouse
    f4 = safe_run("lighthouse", asyncio.to_thread(lighthouse.run_lighthouse, state['url'], state['scan_id']))
    
    # 5. Heatmaps (with extra error handling)
    f5 = safe_run("heatmaps", asyncio.to_thread(heatmaps.generate_heatmaps, state['artifact'].screenshot_bytes, state['artifact'].clickable_elements, state['scan_id']))
    
    # 6. ZAP
    f6 = safe_run("zap_security", asyncio.to_thread(security_zap.run_zap_scan, state['url'], state['scan_id']))
    
    results = await asyncio.gather(f1, f2, f3, f4, f5, f6)
    
    # Unpack results
    sec_res, seo_res, acc_res, lh_res, hm_res, zap_res = results
    
    result_list = []
    
    # Security
    if isinstance(sec_res, dict) and "error" in sec_res:
        result_list.append({"module_name": "security_hygiene", "status": "failed", "result_json": sec_res})
    else:
        result_list.append({"module_name": "security_hygiene", "status": "completed", "result_json": asdict(sec_res)})
    
    # SEO
    if isinstance(seo_res, dict) and "error" in seo_res:
        result_list.append({"module_name": "analytics_seo", "status": "failed", "result_json": seo_res})
    else:
        result_list.append({"module_name": "analytics_seo", "status": "completed", "result_json": asdict(seo_res)})
    
    # Accessibility
    if isinstance(acc_res, dict) and "error" in acc_res:
        result_list.append({"module_name": "accessibility", "status": "failed", "result_json": acc_res})
    else:
        result_list.append({"module_name": "accessibility", "status": "completed", "result_json": asdict(acc_res)})
    
    # Lighthouse
    if isinstance(lh_res, dict) and "error" in lh_res:
        result_list.append({"module_name": "lighthouse", "status": "failed", "result_json": lh_res})
    else:
        # Save full report
        if lh_res.full_report:
            report_bytes = json.dumps(lh_res.full_report).encode('utf-8')
            await asyncio.to_thread(save_file, state['scan_id'], "lighthouse_report", report_bytes, "application/json")
            
        lh_dict = asdict(lh_res)
        lh_dict['lighthouse_report_url'] = get_file_url(state['scan_id'], "lighthouse_report")
        del lh_dict['full_report'] # Remove full report from result JSON
        
        result_list.append({"module_name": "lighthouse", "status": "completed", "result_json": lh_dict})
    
    # Heatmaps
    if isinstance(hm_res, dict) and "error" in hm_res:
        result_list.append({"module_name": "heatmaps", "status": "failed", "result_json": hm_res})
    else:
        # Save heatmaps
        if hm_res.attention_heatmap_bytes:
            await asyncio.to_thread(save_file, state['scan_id'], "attention_heatmap", hm_res.attention_heatmap_bytes, "image/jpeg")
        if hm_res.click_heatmap_bytes:
            await asyncio.to_thread(save_file, state['scan_id'], "click_heatmap", hm_res.click_heatmap_bytes, "image/jpeg")
            
        hm_dict = asdict(hm_res)
        hm_dict['attention_heatmap_url'] = get_file_url(state['scan_id'], "attention_heatmap")
        hm_dict['click_heatmap_url'] = get_file_url(state['scan_id'], "click_heatmap")
        del hm_dict['attention_heatmap_bytes']
        del hm_dict['click_heatmap_bytes']
        
        result_list.append({"module_name": "heatmaps", "status": "completed", "result_json": hm_dict})
    
    # ZAP
    if isinstance(zap_res, dict) and "error" in zap_res:
        result_list.append({"module_name": "zap_security", "status": "failed", "result_json": zap_res})
    else:
        result_list.append({"module_name": "zap_security", "status": zap_res.status, "result_json": asdict(zap_res)})
    
    return {"results": result_list}

# Redefine graph with super node
workflow_parallel = StateGraph(ScanState)
workflow_parallel.add_node("render_page", render_page_node)
workflow_parallel.add_node("analyze_parallel", analyze_parallel_node)
workflow_parallel.add_node("aggregate_report", aggregate_report_node)

workflow_parallel.set_entry_point("render_page")
workflow_parallel.add_edge("render_page", "analyze_parallel")
workflow_parallel.add_edge("analyze_parallel", "aggregate_report")
workflow_parallel.add_edge("aggregate_report", END)

app = workflow_parallel.compile()
