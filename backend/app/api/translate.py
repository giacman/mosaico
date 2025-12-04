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
    
    # Use gemini-2.5-pro for higher quality transcreation
    # Pro model is better at cultural nuances and creative adaptation
    response_text = await ai_client.generate_content(
        prompt=prompt,
        temperature=0.5,  # Higher for more creative, natural transcreation
        response_mime_type="application/json",
        use_flash=False  # Use Pro model for better transcreation quality
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
    """
    Build transcreation prompt using best practices from Anthropic and Google.
    Focuses on cultural adaptation over literal translation.
    """
    
    target_lang_name = LANGUAGE_NAMES.get(target_language, target_language.upper())
    source_instruction = f"from {LANGUAGE_NAMES.get(source_language, source_language)}" if source_language else "(auto-detect source language)"
    
    tone_instruction = ""
    if maintain_tone:
        tone_instruction = """
TONE PRESERVATION:
- Match the original formality level (formal ↔ casual)
- Preserve brand voice characteristics
- Maintain emotional register (enthusiastic, serious, playful, etc.)"""
    
    # Enhanced language-specific guidance with concrete examples
    language_guidance = {
        "de": """
German-Specific Guidelines:
- Verbs for "enjoy": Use "genießen" (experiences/content), NOT "schmecken" (food only)
  Example: "Enjoy exclusive content" → "Genießen Sie exklusive Inhalte" ✓
  WRONG: "Schmecken Sie exklusive Inhalte" ✗
- Compound words: Use natural German compounds (e.g., "Kauferlebnis" not "Kauf Erlebnis")
- Formality: Use "Sie" for professional/marketing content unless explicitly casual
- Imperative: Use polite forms ("Entdecken Sie" not "Entdeck")""",
        
        "fr": """
French-Specific Guidelines:
- Style: Embrace elegant, flowing expressions natural to French marketing
- Anglicisms: Avoid unless widely accepted (e.g., "smartphone" OK, "shopping" → "achats")
- Formality: "vous" for professional tone, "tu" only if source is clearly casual
- Word order: French often inverts subject-verb for elegance in marketing""",
        
        "es": """
Spanish-Specific Guidelines:
- Tone: Use warm, engaging expressions typical of Spanish marketing
- Regional: Consider Spain vs Latin America vocabulary (ordenador vs computadora)
- Imperative: Use inclusive forms ("Descubre" works for both tú/usted contexts)
- Emotion: Spanish marketing is more expressive - embrace it!""",
        
        "pt": """
Portuguese-Specific Guidelines:
- Variant: Consider Brazilian (você/seu) vs European (tu/teu) Portuguese
- Formality: Brazilian marketing often uses "você" (more casual but still professional)
- Expressions: Use natural Portuguese metaphors, not literal translations
- Gerunds: Portuguese uses them differently than English - adapt naturally""",
        
        "it": """
Italian-Specific Guidelines:
- Style: Embrace expressive, emotional language natural to Italian
- Metaphors: Use Italian cultural references (calcio, cibo, famiglia resonate)
- Formality: "Lei" for professional, "tu" for casual (context-dependent)
- Enthusiasm: Italian marketing is passionate - don't tone it down"""
    }
    
    lang_guidance = language_guidance.get(target_language.lower(), "")
    
    # Core prompt with enhanced structure (Anthropic-inspired)
    prompt = f"""You are a professional cultural translator specializing in {content_type} content.

Your expertise is TRANSCREATION, not literal translation. This means preserving the INTENT and EMOTIONAL IMPACT while adapting the expression for the target culture.

=== TASK ===
Transcreate the following text to {target_lang_name} {source_instruction}.
{tone_instruction}

=== YOUR APPROACH ===
Before translating, ask yourself:
1. What is the core message and emotion this text conveys?
2. How would a native {target_lang_name} marketer express this same idea?
3. Are there idioms, metaphors, or cultural references that need adaptation?
4. Does this sound natural when read aloud by a native speaker?

=== CRITICAL RULES ===
✓ DO:
  - Write as a native {target_lang_name} copywriter would originally write it
  - Adapt idioms and metaphors to cultural equivalents
  - Rewrite completely if literal translation sounds awkward
  - Maintain marketing effectiveness and persuasive power
  - Consider context (food/experience/emotion) for word choice

✗ DON'T:
  - Translate word-for-word if it sounds unnatural
  - Use literal translations of idioms
  - Ignore cultural context
  - Lose emotional impact for the sake of accuracy
  - Use formal terms where casual fits better (or vice versa)

{lang_guidance}

=== INPUT TEXT ===
"{text}"

=== OUTPUT REQUIREMENTS ===
Return ONLY valid JSON (no markdown, no explanations):
{{
  "translated_text": "your transcreated text here",
  "detected_source_language": "ISO language code"
}}

Think step-by-step: understand intent → find natural expression → verify it sounds native."""
    
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
        
        # Use gemini-2.5-pro for higher quality transcreation
        # Pro model better at cultural nuances and creative adaptation
        response_text = await vertex_client.generate_content(
            prompt=prompt,
            temperature=0.5,  # Higher for more creative, natural transcreation
            response_mime_type="application/json",
            use_flash=False  # Use Pro model for better transcreation quality
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
            
            # Use gemini-2.5-pro for higher quality transcreation
            response_text = await vertex_client.generate_content(
                prompt=prompt,
                temperature=0.5,  # Higher for more creative, natural transcreation
                response_mime_type="application/json",
                use_flash=False  # Use Pro model for better transcreation quality
            )
            
            response_data = json.loads(response_text)
            return response_data.get("translated_text", text)
        
        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {target_language}: {str(e)}")
            logger.warning(f"Raw response (first 500 chars): {response_text[:500]}")
            
            # Try to extract translated_text even if JSON is malformed
            import re
            match = re.search(r'"translated_text"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', response_text, re.DOTALL)
            if match and attempt == max_retries - 1:
                extracted_text = match.group(1).replace('\\"', '"').replace('\\n', '\n')
                logger.info(f"Extracted text from malformed JSON: {extracted_text[:100]}")
                return extracted_text
            
            if attempt == max_retries - 1:
                logger.error(f"Failed to translate to {target_language} after {max_retries} attempts")
                logger.error(f"Full raw response: {response_text}")
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
