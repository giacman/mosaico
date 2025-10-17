"""
Vertex AI Client Setup
Modern approach - NO LangChain, direct Vertex AI SDK
"""
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from app.core.config import settings
import logging
import os
import json
import httpx
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Wrapper for Vertex AI client with rate limiting and error handling"""
    
    def __init__(self):
        """Initialize Vertex AI client"""
        
        # Check for explicit credentials (Service Account for local dev)
        creds_path = settings.google_application_credentials
        
        if creds_path and os.path.exists(creds_path):
            # Use explicit Service Account credentials (local dev)
            logger.info(f"Using Service Account credentials from: {creds_path}")
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        else:
            # Use Application Default Credentials (Cloud Run or ADC)
            logger.info("Using Application Default Credentials (ADC)")
        
        # Initialize Vertex AI
        try:
            vertexai.init(
                project=settings.gcp_project_id,
                location=settings.gcp_location
            )
            logger.info(f"Vertex AI initialized for project: {settings.gcp_project_id}")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI client: {str(e)}")
            raise
    
    async def generate_content(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_mime_type: str = "application/json",
        use_flash: bool = False
    ) -> str:
        """
        Generate content using Vertex AI
        
        Args:
            prompt: The prompt text
            model: Model name (defaults to settings.vertex_ai_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum output tokens
            response_mime_type: Output format (application/json or text/plain)
            use_flash: If True, use gemini-2.5-flash instead of gemini-2.5-pro
        
        Returns:
            Generated text content
        """
        # Use Flash model if requested, otherwise use provided model or default
        if use_flash:
            model_name = settings.vertex_ai_model_flash
        else:
            model_name = model or settings.vertex_ai_model
        
        try:
            # Create model instance
            generative_model = GenerativeModel(model_name)
            
            # Configure generation
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type=response_mime_type
            )
            
            # Generate content asynchronously
            response = await generative_model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Error generating content with {model_name}: {str(e)}")
            raise

    async def generate_from_image_and_text(
        self,
        prompt: str,
        image_data: bytes,
        image_mime_type: str = "image/jpeg",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_mime_type: str = "application/json"
    ) -> str:
        """
        Generate content from a multimodal input (image and text).
        """
        model_name = model or settings.vertex_ai_model
        
        try:
            generative_model = GenerativeModel(model_name)
            
            # Prepare the multimodal content
            image_part = Part.from_data(data=image_data, mime_type=image_mime_type)
            prompt_part = Part.from_text(prompt)
            
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type=response_mime_type
            )
            
            response = generative_model.generate_content(
                [image_part, prompt_part],
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content from image with {model_name}: {str(e)}")
            raise
    
    async def generate_with_fixing(
        self,
        prompt: str,
        expected_variations: int,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        image_url: str | None = None,
        model: str | None = None,
        response_mime_type: str = "application/json",
    ) -> str:
        model_name = model or settings.vertex_ai_model
        generative_model = GenerativeModel(model_name)
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type=response_mime_type,
            top_p=0.95,  # Add nucleus sampling for more diversity
            top_k=40,    # Add top-k sampling for variety
        )

        final_prompt = [Part.from_text(prompt)]

        if image_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                image_part = Part.from_data(
                    response.content, mime_type=response.headers["Content-Type"]
                )
                final_prompt.insert(0, image_part)
                logger.info(f"Image loaded from {image_url} and added to prompt.")
            except httpx.HTTPStatusError as e:
                logger.error(f"Error downloading image from {image_url}: {e}")
                # Decide how to handle this - maybe proceed without the image?
                # For now, we'll let it raise or you could return an error message
                raise
            except Exception as e:
                logger.error(f"An unexpected error occurred while handling image: {e}")
                raise

        for attempt in range(1, 4):  # 1 initial attempt + 2 fixing attempts
            try:
                response_text = await self._generate_content_with_retry(
                    generative_model, final_prompt, generation_config
                )

                # Validate JSON and variation count
                parsed_json = json.loads(response_text)
                if (
                    "variations" in parsed_json
                    and isinstance(parsed_json["variations"], list)
                    and len(parsed_json["variations"]) >= expected_variations
                ):
                    logger.info(f"Successfully generated and validated JSON.")
                    return response_text
                else:
                    logger.warning(
                        f"Attempt {attempt} produced valid JSON but did not meet variation count expectations."
                    )
                    # This could be a case for a more specific fixing prompt
                    # For now, we rely on the generic fixing prompt to guide the model

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Attempt {attempt} failed with error: {str(e)}. Trying to fix..."
                )
                fixing_prompt = self._create_fixing_prompt(prompt, response_text)
                final_prompt = [Part.from_text(fixing_prompt)]  # For fixing, we only use text
            except Exception as e:
                logger.error(f"An unexpected error occurred during generation: {e}")
                raise

        logger.error("Failed to generate valid JSON after multiple attempts.")
        raise HTTPException(
            status_code=500, detail="Failed to generate valid content from the model."
        )

    def _create_fixing_prompt(self, original_prompt: str, malformed_json: str) -> str:
        return f"""
The original prompt was:
---
{original_prompt}
---

The model produced the following malformed JSON:
---
{malformed_json}
---

Please fix the JSON. Pay close attention to escaping special characters like newlines (\\n) and double quotes (\\") within string values.
Ensure the output is a single, valid JSON object that fulfills the original prompt's requirements.
"""

    async def _generate_content_with_retry(
        self,
        model: GenerativeModel,
        prompt: list,
        generation_config: GenerationConfig,
        max_retries: int = 2,
    ):
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = await model.generate_content_async(
                    prompt, generation_config=generation_config
                )
                return response.text
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1} failed with error: {str(e)}. Retrying..."
                )
                await asyncio.sleep(1)  # simple backoff
        raise last_exception

    async def translate_text(
        self,
        texts: list[str],
        target_language: str,
        source_language: str | None = None,
        model: str | None = None,
    ) -> list[str]:
        model_name = model or settings.vertex_ai_model
        try:
            model = GenerativeModel(model_name)
            results = await model.translate_async(
                contents=texts,
                target_language_code=target_language,
                source_language_code=source_language,
            )
            return [result.translated_text for result in results]
        except Exception as e:
            logger.error(f"Error translating text with {model_name}: {str(e)}")
            raise

    async def refine_text(
        self,
        prompt: str,
        schema: dict,
        max_retries: int = 2,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content with self-healing JSON parsing
        Pattern from InventioHub but without LangChain OutputFixingParser
        
        Args:
            prompt: The prompt with schema instructions
            schema: JSON schema dict for validation error messages
            max_retries: Maximum retry attempts
            temperature: Sampling temperature
        
        Returns:
            Valid JSON string
        """
        last_error = None
        current_prompt = prompt
        
        for attempt in range(max_retries + 1):
            response_text = ""
            try:
                response_text = await self.generate_content(
                    prompt=current_prompt,
                    temperature=temperature,
                    response_mime_type="application/json"
                )
                
                # Validate JSON format
                json.loads(response_text)
                
                return response_text
            
            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed with error: {e}. Trying to fix...")
                    
                    fix_prompt = f"""The following JSON output is malformed or invalid:

{response_text if response_text else 'No output generated'}

Error: {str(e)}

Expected schema:
{json.dumps(schema)}

Please fix the JSON and return ONLY valid JSON matching the schema above.
Ensure all special characters within strings are properly escaped (e.g., newlines as \\n, quotes as \\").
NO markdown formatting, NO explanations, ONLY the JSON object."""
                    
                    current_prompt = fix_prompt
                else:
                    logger.error(f"All {max_retries + 1} attempts failed. Last error: {last_error}")
                    raise last_error
        
        raise last_error # Should not be reached


# Global client instance
vertex_client = VertexAIClient()

def get_client() -> VertexAIClient:
    return vertex_client
