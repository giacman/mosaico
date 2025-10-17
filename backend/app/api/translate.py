"""
Translate Endpoint
Contextual translation maintaining tone and formality
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json
import asyncio
from pydantic import BaseModel
from typing import List, Dict

from app.models.schemas import TranslateRequest, TranslateResponse
from app.core.vertex_ai import vertex_client
from app.core.config import settings
from app.utils.notifications import notify_translation_completed

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


async def translate_text_content(
    text: str,
    target_language: str,
    source_language: str = "EN",
    ai_client=None
) -> str:
    """
    Helper function to translate text content
    Used by both standalone endpoint and project translation
    """
    if ai_client is None:
        ai_client = vertex_client
    
    prompt = build_translation_prompt(
        text=text,
        target_language=target_language.lower(),
        source_language=source_language.lower(),
        maintain_tone=True,
        content_type="newsletter"
    )
    
    # Use generate_content instead of generate_with_fixing for translation
    # (no need for variation count validation)
    response_text = await ai_client.generate_content(
        prompt=prompt,
        temperature=0.3,
        response_mime_type="application/json"
    )
    
    response_data = json.loads(response_text)
    return response_data.get("translated_text", text)


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
        
        # Use generate_content instead of generate_with_fixing for translation
        # (no need for variation count validation)
        response_text = await vertex_client.generate_content(
            prompt=prompt,
            temperature=0.3,  # Lower for more accurate translation
            response_mime_type="application/json"
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


# Batch translation models
class TextToTranslate(BaseModel):
    key: str
    content: str


class BatchTranslateRequest(BaseModel):
    texts: List[TextToTranslate]
    target_languages: List[str]


class BatchTranslateResponse(BaseModel):
    translations: Dict[str, Dict[str, str]]  # {component_key: {lang: translated_text}}


async def translate_single_with_retry(
    text: str,
    target_language: str,
    max_retries: int = 3
) -> str:
    """
    Translate a single text with retry logic for malformed JSON
    """
    for attempt in range(max_retries):
        try:
            prompt = build_translation_prompt(
                text=text,
                target_language=target_language.lower(),
                source_language="auto",
                maintain_tone=True,
                content_type="newsletter"
            )
            
            response_text = await vertex_client.generate_content(
                prompt=prompt,
                temperature=0.3,
                response_mime_type="application/json"
            )
            
            response_data = json.loads(response_text)
            return response_data.get("translated_text", text)
        
        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {target_language}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to translate to {target_language} after {max_retries} attempts")
                return f"[Translation failed: {text[:50]}...]"
            await asyncio.sleep(0.5)  # Brief delay before retry
        
        except Exception as e:
            logger.error(f"Error translating to {target_language}: {str(e)}")
            return f"[Translation error: {text[:50]}...]"


@router.post("/translate/batch", response_model=BatchTranslateResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def batch_translate(
    request: Request,
    req: BatchTranslateRequest
) -> BatchTranslateResponse:
    """
    Batch translate multiple texts to multiple languages in parallel
    Much faster than individual requests
    """
    try:
        logger.info(
            f"Batch translating {len(req.texts)} texts to {len(req.target_languages)} languages "
            f"({len(req.texts) * len(req.target_languages)} total translations)"
        )
        
        translations: Dict[str, Dict[str, str]] = {}
        
        # Create all translation tasks
        tasks = []
        task_metadata = []
        
        for text_item in req.texts:
            translations[text_item.key] = {}
            
            for lang in req.target_languages:
                task = translate_single_with_retry(text_item.content, lang)
                tasks.append(task)
                task_metadata.append((text_item.key, lang))
        
        # Execute all translations in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to structure
        for (key, lang), result in zip(task_metadata, results):
            if isinstance(result, Exception):
                logger.error(f"Exception translating {key} to {lang}: {str(result)}")
                translations[key][lang] = f"[Error: {str(result)[:50]}]"
            else:
                translations[key][lang] = result
        
        logger.info(f"Batch translation completed successfully")
        
        # Send Slack notification (non-blocking)
        asyncio.create_task(
            notify_translation_completed(
                project_name="Unknown",  # Will be enriched when we have project context
                language_count=len(req.target_languages),
                component_count=len(req.texts),
                user_email=None
            )
        )
        
        return BatchTranslateResponse(translations=translations)
    
    except Exception as e:
        logger.error(f"Error in batch_translate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
