import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class ElementClickScore:
    tag: str
    text: str
    score: float
    rect: Dict[str, float]

@dataclass
class HeatmapResult:
    attention_heatmap_bytes: bytes
    click_heatmap_bytes: bytes
    elements: List[ElementClickScore]

def decode_image(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def encode_image(image: np.ndarray) -> bytes:
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        raise ValueError("Could not encode image")
    return encoded_image.tobytes()

def compute_attention_map(img: np.ndarray) -> np.ndarray:
    """
    Computes a simple saliency map based on edges and intensity.
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection (Canny)
        edges = cv2.Canny(gray, 100, 200)
        
        # Blur to create a heatmap-like effect
        saliency = cv2.GaussianBlur(edges, (51, 51), 0)
        
        # Normalize to 0-1
        saliency = saliency.astype("float32") / 255.0
        
        return saliency
    except Exception as e:
        print(f"Error computing attention map: {e}")
        h, w = img.shape[:2]
        return np.zeros((h, w), dtype="float32")

def rasterize_click_map(
    img_shape: Tuple[int, int], 
    elements: List[Dict[str, Any]]
) -> Tuple[np.ndarray, List[ElementClickScore]]:
    """
    Creates a heatmap based on clickable elements.
    """
    try:
        h, w = img_shape
        click_map = np.zeros((h, w), dtype="float32")
        
        scored_elements = []
        
        for el in elements:
            rect = el.get('rect')
            if not rect:
                continue
                
            # Simple heuristic: buttons and inputs are "hotter"
            tag = el.get('tag', '').lower()
            score = 0.5
            if tag in ['button', 'input', 'select', 'textarea']:
                score = 0.8
            if el.get('href'):
                score = 0.6
                
            # Add to map
            x = int(rect['x'])
            y = int(rect['y'])
            width = int(rect['width'])
            height = int(rect['height'])
            
            # Ensure within bounds
            x = max(0, min(w-1, x))
            y = max(0, min(h-1, y))
            x2 = max(0, min(w-1, x + width))
            y2 = max(0, min(h-1, y + height))
            
            # Draw rectangle on heatmap
            # Use scalar for grayscale image
            intensity = int(score * 255)
            intensity = max(0, min(255, intensity)) # Ensure valid range
            cv2.rectangle(click_map, (x, y), (x2, y2), intensity, -1)
            
            scored_elements.append(ElementClickScore(
                tag=tag,
                text=el.get('text', '')[:50],
                score=score,
                rect=rect
            ))
            
        # Blur
        click_map = cv2.GaussianBlur(click_map, (101, 101), 0)
        
        # Normalize
        if click_map.max() > 0:
            click_map /= click_map.max()
            
        return click_map, scored_elements
    except Exception as e:
        print(f"Error rasterizing click map: {e}")
        return np.zeros(img_shape, dtype="float32"), []

def overlay_heatmap(original: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    try:
        # Normalize heatmap to 0-255
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        # Apply colormap
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        # Overlay
        return cv2.addWeighted(original, 0.6, heatmap_color, 0.4, 0)
    except Exception as e:
        print(f"Error overlaying heatmap: {e}")
        return original

def generate_heatmaps(screenshot_bytes: bytes, clickable_elements: List[Dict[str, Any]], scan_id: str) -> HeatmapResult:
    """
    Generates attention and click heatmaps.
    """
    try:
        img = decode_image(screenshot_bytes)
        if img is None:
             raise ValueError("Could not decode screenshot bytes")
        
        # 1. Attention Map
        attention_map = compute_attention_map(img)
        attention_overlay = overlay_heatmap(img, attention_map)
        attention_bytes = encode_image(attention_overlay)
        
        # 2. Click Map
        click_map, scored_elements = rasterize_click_map(img.shape[:2], clickable_elements)
        click_overlay = overlay_heatmap(img, click_map)
        click_bytes = encode_image(click_overlay)
        
        return HeatmapResult(
            attention_heatmap_bytes=attention_bytes,
            click_heatmap_bytes=click_bytes,
            elements=scored_elements
        )
    except Exception as e:
        print(f"Error generating heatmaps: {e}")
        return HeatmapResult(
            attention_heatmap_bytes=b"",
            click_heatmap_bytes=b"",
            elements=[]
        )
