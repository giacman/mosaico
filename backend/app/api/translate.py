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
import re
from pydantic import BaseModel
from typing import List, Dict, Optional

from app.models.schemas import TranslateRequest, TranslateResponse
from app.core.vertex_ai import vertex_client
from app.utils.text_limits import clamp_push_text, get_push_limit
from app.core.config import settings
from app.utils.notifications import notify_translation_completed
from app.core.auth import get_current_user, User
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Optional

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
# Limit concurrent Vertex AI requests to avoid rate limits
translate_semaphore = asyncio.Semaphore(10)


class ValidationResult(BaseModel):
    """Result of translation quality validation"""
    is_valid: bool
    confidence_score: float
    naturalness_score: float
    cultural_adaptation_score: float
    tone_score: float
    issues: List[str]
    suggestions: str
    reasoning: str


async def validate_translation(
    source_text: str,
    translated_text: str,
    target_language: str,
    source_language: str = "auto",
    ai_client=None
) -> ValidationResult:
    """
    Validate translation quality using AI reviewer.
    Returns validation result with confidence score and suggestions.
    """
    if ai_client is None:
        ai_client = vertex_client
    
    validation_prompt = build_validation_prompt(
        source_text=source_text,
        translated_text=translated_text,
        target_language=target_language,
        source_language=source_language
    )
    
    try:
        # Use Pro model for validation (needs reasoning capability)
        response_text = await ai_client.generate_content(
            prompt=validation_prompt,
            temperature=0.3,  # Lower for more consistent evaluation
            response_mime_type="application/json",
            use_flash=False  # Use Pro for better evaluation
        )
        
        validation_data = json.loads(response_text)
        return ValidationResult(**validation_data)
    
    except Exception as e:
        logger.warning(f"Validation failed, assuming translation is valid: {str(e)}")
        # Fallback: assume translation is valid if validation fails
        return ValidationResult(
            is_valid=True,
            confidence_score=0.8,  # Neutral score
            naturalness_score=0.8,
            cultural_adaptation_score=0.8,
            tone_score=0.8,
            issues=[],
            suggestions="",
            reasoning="Validation service unavailable, defaulting to valid"
        )


async def translate_with_retry(
    text: str,
    target_language: str,
    source_language: str = "EN",
    validation_feedback: str = "",
    ai_client=None
) -> str:
    """
    Translate text with optional validation feedback from previous attempt.
    
    Args:
        text: Source text to translate
        target_language: Target language code
        source_language: Source language code
        validation_feedback: Feedback from validator to improve translation
        ai_client: AI client to use
    
    Returns:
        Translated text
    """
    if ai_client is None:
        ai_client = vertex_client
    
    base_prompt = build_translation_prompt(
        text=text,
        target_language=target_language.lower(),
        source_language=source_language.lower(),
        maintain_tone=True,
        content_type="newsletter"
    )
    
    # Add validation feedback if this is a retry
    if validation_feedback:
        prompt = f"""{base_prompt}

=== IMPORTANT: IMPROVE BASED ON FEEDBACK ===
Your previous translation had issues. Address these problems:

{validation_feedback}

Make sure your new translation fixes these specific issues while maintaining quality."""
    else:
        prompt = base_prompt
    
    # Use gemini-2.5-pro for higher quality transcreation
    # Increase max_tokens to handle longer body text translations
    response_text = await ai_client.generate_content(
        prompt=prompt,
        temperature=0.5,  # Higher for more creative, natural transcreation
        max_tokens=4096,  # Increased from default 2048 for longer translations
        response_mime_type="application/json",
        use_flash=False  # Use Pro model for better transcreation quality
    )
    
    try:
        response_data = json.loads(response_text)
        return response_data.get("translated_text", text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed in translate_with_retry: {str(e)} | Response: {response_text}")
        raise  # Re-raise to be handled by caller


async def translate_text_content(
    text: str,
    target_language: str,
    source_language: str = "EN",
    ai_client=None,
    use_validation: bool = True,
    max_retries: int = 1,
    component_type: str | None = None,
    content_type: str | None = None
) -> str:
    """
    Helper function to translate text content with optional validation.
    
    Args:
        text: Source text to translate
        target_language: Target language code
        source_language: Source language code
        ai_client: AI client to use
        use_validation: Whether to validate and retry if quality is low
        max_retries: Maximum number of retry attempts (default: 1)
    
    Returns:
        Translated text
    """
    if ai_client is None:
        ai_client = vertex_client
    
    # Step 1: Initial translation
    translation = await translate_with_retry(
        text=text,
        target_language=target_language,
        source_language=source_language,
        ai_client=ai_client
    )
    translation = strip_trailing_period(translation, component_type)

    limit = get_push_limit(component_type, content_type)
    if limit and len(translation) > limit and max_retries > 0:
        feedback = f"Too long. Must be <= {limit} characters for {component_type}."
        translation = await translate_with_retry(
            text=text,
            target_language=target_language,
            source_language=source_language,
            validation_feedback=feedback,
            ai_client=ai_client
        )
        translation = strip_trailing_period(translation, component_type)

    translation = clamp_push_text(translation, component_type, content_type)
    
    # If validation is disabled, return immediately
    if not use_validation:
        return translation
    
    # Step 2: Validate translation quality
    try:
        validation = await validate_translation(
            source_text=text,
            translated_text=translation,
            target_language=target_language,
            source_language=source_language,
            ai_client=ai_client
        )
        
        logger.info(
            f"Translation validation: confidence={validation.confidence_score:.2f}, "
            f"naturalness={validation.naturalness_score:.2f}, "
            f"issues={len(validation.issues)}"
        )
        
        # Step 3: Retry if confidence is low and we have retries left
        if validation.confidence_score < 0.7 and max_retries > 0:
            logger.warning(
                f"Low confidence score ({validation.confidence_score:.2f}), "
                f"retrying with feedback. Issues: {validation.issues}"
            )
            
            # Prepare feedback for retry
            feedback = f"""Issues identified:
{chr(10).join(f'- {issue}' for issue in validation.issues)}

Suggestions: {validation.suggestions}

Reasoning: {validation.reasoning}"""
            
            # Retry with feedback
            improved_translation = await translate_with_retry(
                text=text,
                target_language=target_language,
                source_language=source_language,
                validation_feedback=feedback,
                ai_client=ai_client
            )
            improved_translation = strip_trailing_period(improved_translation, component_type)
            improved_translation = clamp_push_text(improved_translation, component_type, content_type)
            
            logger.info(f"Retry completed, using improved translation")
            return improved_translation
        
        # Return original translation if quality is good or no retries left
        return translation
    
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}, using translation without validation")
        return translation


LANGUAGE_NAMES = {
    "it": "Italian",
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese"
}

COMPONENT_TYPES = ("subject", "pre_header", "title", "body", "cta")


def extract_component_type(key: str | None) -> str | None:
    """
    Extract component type from a batch translation key.
    Examples: "header:subject:1" -> subject, "section_2:pre_header:1" -> pre_header
    """
    if not key:
        return None
    lowered = key.lower()
    if "pre_header" in lowered:
        return "pre_header"
    for comp in COMPONENT_TYPES:
        if comp in lowered:
            return comp
    return None


def strip_trailing_period(text: str, component_type: str | None) -> str:
    """
    Remove trailing period/full-stop for header-like components.
    """
    if not text or not component_type:
        return text
    if component_type not in ("subject", "title", "pre_header", "cta"):
        return text
    # Remove trailing period variants (., 。, ．, ｡) plus whitespace
    return re.sub(r"[\.。\uFF0E\uFF61]+\s*$", "", text).rstrip()


def build_validation_prompt(
    source_text: str,
    translated_text: str,
    target_language: str,
    source_language: str = "auto"
) -> str:
    """
    Build prompt for validating translation quality.
    Returns a validation with confidence score and issues identified.
    """
    target_lang_name = LANGUAGE_NAMES.get(target_language, target_language.upper())
    source_lang_name = LANGUAGE_NAMES.get(source_language, source_language.upper()) if source_language != "auto" else "detected language"
    
    prompt = f"""You are a professional translation quality reviewer specializing in marketing content.

Your task is to evaluate the quality of a translation and provide a confidence score.

=== EVALUATION TASK ===
Source text ({source_lang_name}): "{source_text}"
Translation ({target_lang_name}): "{translated_text}"

=== EVALUATION CRITERIA ===

1. NATURALNESS (40 points)
   - Does it sound like it was written by a native {target_lang_name} speaker?
   - Is the grammar and syntax natural and fluent?
   - Would a native speaker use these exact words/phrases?

2. CULTURAL ADAPTATION (30 points)
   - Are idioms and metaphors adapted (not literal)?
   - Are cultural references appropriate?
   - Context-aware word choice? (e.g., "enjoy" for food vs content)

3. TONE & FORMALITY (20 points)
   - Does it maintain the original tone?
   - Is formality level appropriate? (formal/casual)
   - Brand voice preserved?

4. ACCURACY (10 points)
   - Core message preserved?
   - No meaning lost or added?
   - Marketing impact maintained?

=== COMMON PITFALLS TO CHECK ===
- Literal word-for-word translation (BAD)
- Wrong verb choice based on context (e.g., German "schmecken" for non-food)
- Unnatural phrasing or word order
- Lost emotional impact
- Inappropriate formality level

=== OUTPUT REQUIREMENTS ===
Provide your evaluation as JSON:

{{
  "is_valid": true/false,
  "confidence_score": 0.0-1.0,
  "naturalness_score": 0.0-1.0,
  "cultural_adaptation_score": 0.0-1.0,
  "tone_score": 0.0-1.0,
  "issues": ["issue1", "issue2"],
  "suggestions": "How to improve if confidence < 0.7",
  "reasoning": "Brief explanation of your evaluation"
}}

Scoring guide:
- 0.9-1.0: Excellent, sounds native
- 0.7-0.9: Good, minor improvements possible
- 0.5-0.7: Acceptable, has issues
- 0.0-0.5: Poor, needs rewrite

Be critical but fair. Return ONLY the JSON object."""
    
    return prompt


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
Return ONLY valid JSON. 
IMPORTANT: Ensure all special characters like newlines (\\n) and double quotes (\\") within the translated text are properly escaped.
The output MUST be a single JSON object with NO markdown formatting and NO explanations.

Structure:
{{
  "translated_text": "your transcreated text here",
  "detected_source_language": "ISO language code"
}}

Think step-by-step: understand intent → find natural expression → verify it sounds native. Return JSON object."""
    
    return prompt


@router.post("/translate", response_model=TranslateResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def translate_text(
    request: Request,
    req: TranslateRequest
) -> TranslateResponse:
    """
    Translate text with Sequential Validation Chain
    
    Now includes:
    - Translation with enhanced prompt
    - Quality validation with confidence scoring
    - Auto-retry if confidence < 0.7
    """
    try:
        logger.info(f"Translating to {req.target_language} | Type: {req.content_type} | Validation: enabled")
        
        # Use translate_text_content with validation enabled
        translated_text = await translate_text_content(
            text=req.text,
            target_language=req.target_language,
            source_language=req.source_language or "auto",
            ai_client=vertex_client,
            use_validation=True,  # Enable Sequential Validation
            max_retries=1,  # Allow 1 retry if validation fails
            component_type=req.component_type,
            content_type=req.content_type
        )
        
        return TranslateResponse(
            translated_text=translated_text,
            original_text=req.text,
            source_language=req.source_language or "auto",
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
    project_id: Optional[int] = None  # Optional project ID for notifications
    user_email: Optional[str] = None  # Optional user email for notifications
    content_type: Optional[str] = None  # Optional content type for constraints


class BatchTranslateResponse(BaseModel):
    translations: Dict[str, Dict[str, str]]  # {component_key: {lang: translated_text}}


async def translate_single_with_retry(
    text: str,
    target_language: str,
    max_retries: int = 3,
    use_validation: bool = True,
    source_language: str = "auto",
    component_type: str | None = None,
    content_type: str | None = None
) -> str:
    """
    Translate a single text with Sequential Validation Chain.
    
    Args:
        text: Text to translate
        target_language: Target language code
        max_retries: Max retries for JSON decode errors (default: 3)
        use_validation: Enable quality validation and smart retry (default: True)
    
    Returns:
        Translated text
    """
    try:
        async with translate_semaphore:
            # Use the new translate_text_content with validation
            translation = await translate_text_content(
                text=text,
                target_language=target_language,
                source_language=source_language,
                ai_client=vertex_client,
                use_validation=use_validation,
                max_retries=1 if use_validation else 0,  # Validation has its own retry logic
                component_type=component_type,
                content_type=content_type
            )
            return translation
    
    except json.JSONDecodeError as e:
        # Strict failure: do not return original text
        logger.error(f"JSON decode failed for {target_language}: {str(e)}")
        return f"__TRANSLATION_FAILED__:{text[:50]}"
    
    except Exception as e:
        logger.error(f"Error translating to {target_language}: {str(e)}")
        return f"__TRANSLATION_FAILED__:{str(e)[:50]}"


@router.post("/translate/batch", response_model=BatchTranslateResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def batch_translate(
    request: Request,
    req: BatchTranslateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        component_type_lookup = {item.key: extract_component_type(item.key) for item in req.texts}
        normalized_languages = [lang.lower() for lang in req.target_languages]
        pivot_language = "it" if "it" in normalized_languages else None
        other_languages = [lang for lang in normalized_languages if lang != "it"]

        # Two-step translation: EN -> IT, then IT -> others (if Italian requested)
        if pivot_language and other_languages:
            logger.info(f"Batch translate pivot enabled: EN -> IT -> {', '.join(other_languages)}")
            italian_tasks = []
            italian_task_keys = []
            for text_item in req.texts:
                translations[text_item.key] = {}
                italian_tasks.append(
                    translate_single_with_retry(
                        text_item.content,
                        "it",
                        source_language="en",
                        component_type=component_type_lookup.get(text_item.key),
                        content_type=req.content_type
                    )
                )
                italian_task_keys.append(text_item.key)

            italian_results = await asyncio.gather(*italian_tasks, return_exceptions=True)
            italian_lookup: Dict[str, str] = {}

            for key, result in zip(italian_task_keys, italian_results):
                if isinstance(result, Exception):
                    logger.error(f"Exception translating {key} to it: {str(result)}")
                    translations[key]["it"] = f"__TRANSLATION_FAILED__:{str(result)[:50]}"
                else:
                    translations[key]["it"] = result
                    italian_lookup[key] = result

            tasks = []
            task_metadata = []
            for text_item in req.texts:
                component_type = component_type_lookup.get(text_item.key)
                italian_text = italian_lookup.get(text_item.key)
                source_text = italian_text if italian_text and not italian_text.startswith("__TRANSLATION_FAILED__") else text_item.content
                source_language = "it" if source_text == italian_text else "en"
                logger.info(
                    f"Batch translate source for {text_item.key}: {source_language} -> {', '.join(other_languages)}"
                )

                for lang in other_languages:
                    tasks.append(
                        translate_single_with_retry(
                            source_text,
                            lang,
                            source_language=source_language,
                        component_type=component_type,
                        content_type=req.content_type
                        )
                    )
                    task_metadata.append((text_item.key, lang))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (key, lang), result in zip(task_metadata, results):
                if isinstance(result, Exception):
                    logger.error(f"Exception translating {key} to {lang}: {str(result)}")
                    translations[key][lang] = f"__TRANSLATION_FAILED__:{str(result)[:50]}"
                else:
                    translations[key][lang] = result

        else:
            logger.info(f"Batch translate direct mode: EN -> {', '.join(normalized_languages)}")
            # Single-step translation from EN to requested languages
            tasks = []
            task_metadata = []
            for text_item in req.texts:
                translations[text_item.key] = {}
                component_type = component_type_lookup.get(text_item.key)
                for lang in normalized_languages:
                    tasks.append(
                        translate_single_with_retry(
                            text_item.content,
                            lang,
                            source_language="en",
                        component_type=component_type,
                        content_type=req.content_type
                        )
                    )
                    task_metadata.append((text_item.key, lang))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (key, lang), result in zip(task_metadata, results):
                if isinstance(result, Exception):
                    logger.error(f"Exception translating {key} to {lang}: {str(result)}")
                    translations[key][lang] = f"__TRANSLATION_FAILED__:{str(result)[:50]}"
                else:
                    translations[key][lang] = result
        
        logger.info(f"Batch translation completed successfully")
        
        # Send Slack notification if project_id is provided
        if req.project_id:
            try:
                from app.db.models import Project
                project = db.query(Project).filter(Project.id == req.project_id).first()
                if project:
                    user_email = req.user_email or user.name if hasattr(user, 'name') else None
                    asyncio.create_task(
                        notify_translation_completed(
                            project_name=project.name,
                            project_id=project.id,
                            language_count=len(req.target_languages),
                            component_count=len(req.texts),
                            user_email=user_email
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to send translation notification: {str(e)}")
        
        return BatchTranslateResponse(translations=translations)
    
    except Exception as e:
        logger.error(f"Error in batch_translate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
