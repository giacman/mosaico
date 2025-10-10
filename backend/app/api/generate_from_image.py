"""
Generate from Image Endpoint
Multimodal feature: Generate text from an image URL and a text prompt
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json
import httpx

from app.models.schemas import (
    GenerateFromImageRequest,
    GenerateVariationsResponse  # We can reuse this for the response
)
from app.core.vertex_ai import vertex_client
from app.core.config import settings

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def build_image_generation_prompt(
    text: str,
    count: int,
    tone: str,
    content_type: str
) -> str:
    """Builds the text prompt to accompany the image."""
    return f"""You are a senior copywriter specialized in creating {content_type} content.
Based on the image provided, your task is to generate {count} variations of text for the following instruction.
Maintain a {tone} tone and brand voice consistency.

INSTRUCTION:
"{text}"

GUIDELINES:
- Analyze the image for key themes, products, and ambiance.
- Generate creative and relevant text that aligns with both the image and the instruction.
- Ensure each variation is distinct.
- Output ONLY as a valid JSON array of strings: {{"variations": ["variation 1", "variation 2", ...]}}
"""

async def load_image_from_url(url: str) -> bytes:
    """Asynchronously load image data from a URL."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error loading image from {url}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load image from URL: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error loading image from {url}: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid image URL or network issue: {e}")

@router.post("/generate-from-image", response_model=GenerateVariationsResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def generate_from_image(
    request: Request,
    req: GenerateFromImageRequest
) -> GenerateVariationsResponse:
    """
    Generate text variations from an image and a text prompt.
    """
    try:
        logger.info(f"Generating from image. Prompt: '{req.text}' | Image URL: {req.image_url}")
        
        # 1. Load image data from URL
        image_data = await load_image_from_url(req.image_url)
        
        # 2. Build the text part of the prompt
        prompt = build_image_generation_prompt(
            text=req.text,
            count=req.count,
            tone=req.tone.value,
            content_type=req.content_type.value
        )
        
        # 3. Call the multimodal generation method
        response_text = await vertex_client.generate_from_image_and_text(
            prompt=prompt,
            image_data=image_data,
            temperature=0.8
        )
        
        # 4. Parse and return the response
        response_data = json.loads(response_text)
        variations = response_data.get("variations", [])
        
        logger.info(f"Successfully generated {len(variations)} variations from image.")
        
        return GenerateVariationsResponse(
            variations=variations,
            original_text=req.text,
            tone=req.tone.value
        )
        
    except Exception as e:
        logger.error(f"Error in generate_from_image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
