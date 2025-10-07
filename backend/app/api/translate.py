"""
Translate Endpoint
Contextual translation maintaining tone and formality
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json

from app.models.schemas import TranslateRequest, TranslateResponse
from app.core.vertex_ai import vertex_client
from app.core.config import settings

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


LANGUAGE_NAMES = {
    "it": "Italian",
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese"
}


def build_translation_prompt(
    text: str,
    target_language: str,
    source_language: str | None,
    maintain_tone: bool,
    content_type: str
) -> str:
    """Build prompt for translation"""
    
    target_lang_name = LANGUAGE_NAMES.get(target_language, target_language.upper())
    source_instruction = f"from {LANGUAGE_NAMES.get(source_language, source_language)}" if source_language else "(auto-detect source language)"
    
    tone_instruction = ""
    if maintain_tone:
        tone_instruction = """
IMPORTANT: Maintain the original tone, style, and formality level.
- If the original is casual, keep it casual
- If the original is formal, keep it formal
- Preserve any brand voice characteristics"""
    
    prompt = f"""You are a professional translator specialized in {content_type} content.

Task: Translate the following text to {target_lang_name} {source_instruction}.
{tone_instruction}

Guidelines:
- Preserve the core message and intent
- Adapt idioms and expressions appropriately for the target culture
- Maintain proper grammar and natural flow
- Keep the same level of formality

Text to translate:
"{text}"

Output as JSON matching this structure:
{{
  "translated_text": "translation here",
  "detected_source_language": "language code"
}}

Return ONLY the JSON object, no markdown, no explanations."""
    
    return prompt


@router.post("/translate", response_model=TranslateResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def translate_text(
    request: Request,
    req: TranslateRequest
) -> TranslateResponse:
    """
    Translate text with context and tone preservation
    """
    try:
        logger.info(f"Translating to {req.target_language} | Type: {req.content_type}")
        
        prompt = build_translation_prompt(
            text=req.text,
            target_language=req.target_language,
            source_language=req.source_language,
            maintain_tone=req.maintain_tone,
            content_type=req.content_type.value
        )
        
        response_text = await vertex_client.generate_with_fixing(
            prompt=prompt,
            schema={"translated_text": "string", "detected_source_language": "string"},
            temperature=0.3  # Lower for more accurate translation
        )
        
        response_data = json.loads(response_text)
        
        return TranslateResponse(
            translated_text=response_data["translated_text"],
            original_text=req.text,
            source_language=response_data.get("detected_source_language", req.source_language or "auto"),
            target_language=req.target_language
        )
    
    except Exception as e:
        logger.error(f"Error in translate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
