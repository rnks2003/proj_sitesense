import google.generativeai as genai
from ..config import settings
from typing import List, Dict, Any

def get_model(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(settings.AI_MODEL)

def generate_system_prompt(scan_context: Dict[str, Any]) -> str:
    """
    Generates a system prompt based on the provided scan context.
    """
    if not scan_context:
        return "You are a helpful assistant for SiteSense. The user has not provided any specific scan context."

    url = scan_context.get('url', 'unknown URL')
    
    # Extract scores if available
    scores = "N/A"
    module_results = scan_context.get('module_results', [])
    aggregated = next((r for r in module_results if r.get('module_name') == 'aggregated_report'), None)
    
    if aggregated and 'result_json' in aggregated:
        report = aggregated['result_json']
        overall = report.get('overall_score', 'N/A')
        mod_scores = report.get('module_scores', {})
        scores = f"Overall: {overall}\n"
        for k, v in mod_scores.items():
            scores += f"- {k}: {v}\n"
            
        recommendations = report.get('recommendations', [])
        rec_text = "\n".join([f"- {r.get('category')}: {r.get('text')}" for r in recommendations])
    else:
        scores = "No score data available."
        rec_text = "No recommendations available."

    prompt = f"""
    You are SiteSense AI, an expert web analysis assistant.
    You are analyzing a scan report for the website: {url}
    
    Here are the scan results:
    {scores}
    
    Top Recommendations:
    {rec_text}
    
    Your goal is to help the user understand these results, explain technical terms, and provide actionable advice to improve their website.
    You can also use your general knowledge and Google Search capabilities to provide up-to-date information about web best practices.
    Be concise, professional, and helpful.
    """
    return prompt

async def chat_with_gemini(message: str, history: List[Dict[str, str]], api_key: str, scan_context: Dict[str, Any]) -> str:
    try:
        model = get_model(api_key)
        
        system_prompt = generate_system_prompt(scan_context)
        
        # Convert history to Gemini format
        chat_history = []
        # Add system prompt as the first part of the context if possible, 
        # or just prepend it to the first message. 
        # Gemini 1.5 Pro supports system instructions, but for simplicity via SDK 
        # we can just prepend context.
        
        # Actually, let's just use the chat session
        chat = model.start_chat(history=[])
        
        # Send system prompt as first message (user) -> acknowledge (model)
        # This is a common pattern if system instruction arg isn't used
        # But let's try to just prepend it to the current message for statelessness 
        # or use the history provided.
        
        full_prompt = f"{system_prompt}\n\nUser Question: {message}"
        
        # Reconstruct history
        gemini_history = []
        for msg in history:
            role = "user" if "user" in msg else "model"
            content = msg.get("user") or msg.get("assistant")
            gemini_history.append({"role": role, "parts": [content]})
            
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(full_prompt)
        
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return f"I encountered an error processing your request: {str(e)}"
