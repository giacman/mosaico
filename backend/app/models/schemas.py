"""
Pydantic Models for Mosaico
Inspired by InventioHub but simplified for Add-on use case
"""
from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ToneType(str, Enum):
    """Tone variations for content generation"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    ELEGANT = "elegant"
    DIRECT = "direct"


class ContentType(str, Enum):
    """Content types supported by Mosaico"""
    NEWSLETTER = "newsletter"
    SOCIAL_POST = "social_post"
    PRODUCT_DESCRIPTION = "product_description"
    EDITORIAL = "editorial"


class ComponentType(str, Enum):
    FULL_EMAIL = "full_email" # Kept for potential fallback, but structure is preferred
    SUBJECT = "subject"
    PRE_HEADER = "pre_header"
    TITLE = "title"
    BODY = "body"
    CTA = "cta"


class StructureComponent(BaseModel):
    component: ComponentType
    count: int = Field(default=1, ge=1, le=10)


# ============================================================================
# REQUESTS
# ============================================================================

class GenerateVariationsRequest(BaseModel):
    """Request to generate text variations"""
    text: str = Field(..., description="The instructional text or prompt")
    count: int = Field(default=1, description="Number of variations to generate")
    tone: ToneType = Field(default=ToneType.PROFESSIONAL, description="Tone of voice")
    content_type: ContentType = Field(default=ContentType.NEWSLETTER, description="Content type")
    structure: list[StructureComponent] = Field(..., description="A list of components and their counts to generate in the desired order")
    context: str | None = Field(default=None, description="Optional additional context")
    image_url: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0, description="Temperature for generation (0.0-1.0, default 0.7)")
    use_flash: bool | None = Field(default=False, description="Use Gemini Flash model instead of Pro for faster, cheaper generation")
    use_few_shot: bool | None = Field(default=False, description="Include Few-Shot examples in prompt (for regeneration only, not initial generation)")


class TranslateRequest(BaseModel):
    """Request to translate text"""
    text: str = Field(..., description="Text to translate", min_length=1, max_length=2000)
    target_language: str = Field(..., description="Target language code (e.g., 'it', 'en', 'fr')", min_length=2, max_length=5)
    source_language: str | None = Field(default=None, description="Source language code (auto-detect if None)")
    maintain_tone: bool = Field(default=True, description="Maintain original tone and style")
    content_type: ContentType = Field(default=ContentType.NEWSLETTER, description="Type of content")


class RefineRequest(BaseModel):
    """Request to refine/improve text"""
    text: str = Field(..., description="Text to refine", min_length=1, max_length=2000)
    operation: Literal["shorten", "fix_grammar", "improve_clarity", "make_formal", "make_casual"] = Field(
        ..., 
        description="Type of refinement operation"
    )
    content_type: ContentType = Field(default=ContentType.NEWSLETTER, description="Type of content")


# ============================================================================
# RESPONSES
# ============================================================================

class VariationItem(BaseModel):
    """Single variation item"""
    text: str = Field(..., description="Generated variation text")
    tone: str = Field(..., description="Tone used for this variation")


class GenerateVariationsResponse(BaseModel):
    variations: list[dict[str, str]]
    original_text: str
    tone: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "variations": [
                    {
                        "title": "Scopri la nuova collezione primavera/estate",
                        "body": "La collezione PE2025 ti aspetta",
                        "cta": "Novità stagionali: esplora ora"
                    }
                ],
                "original_text": "Nuova collezione primavera",
                "tone": "professional"
            }
        }


class TranslateResponse(BaseModel):
    """Response with translated text"""
    translated_text: str = Field(..., description="Translated text")
    original_text: str = Field(..., description="Original text")
    source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(..., description="Target language")


class RefineResponse(BaseModel):
    """Response with refined text"""
    refined_text: str = Field(..., description="Refined/improved text")
    original_text: str = Field(..., description="Original text")
    operation: str = Field(..., description="Operation performed")


class GenerateFromImageRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image to process")
    text: str = Field(..., description="The instructional text or prompt to run against the image")
    count: int = Field(default=3, description="Number of variations to generate")
    tone: ToneType = Field(default=ToneType.PROFESSIONAL, description="Tone of voice for the generated text")
    content_type: ContentType = Field(default=ContentType.NEWSLETTER, description="Type of content to generate")
    structure: list[StructureComponent] = Field(..., description="A list of components and their counts to generate in the desired order")
    context: str | None = Field(default=None, description="Optional additional context")


# ============================================================================
# IMAGE TO TEXT (Future - Multimodal)
# ============================================================================

class ImageToTextRequest(BaseModel):
    """Request to generate text from image"""
    image_url: str = Field(..., description="URL of the image to analyze")
    instruction: str = Field(
        default="Generate a compelling product description for this image",
        description="Instruction for what to generate from the image"
    )
    max_length: int = Field(default=200, description="Maximum length of generated text", ge=50, le=500)


class ImageToTextResponse(BaseModel):
    """Response with generated text from image"""
    generated_text: str = Field(..., description="Generated text from image")
    image_url: str = Field(..., description="Original image URL")
