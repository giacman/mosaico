"""
Project-based Generation and Translation Endpoints
Combines AI generation with database persistence
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.vertex_ai import VertexAIClient, get_client
from app.db.session import get_db
from app.db.models import Project, Component, Translation, Image
from app.models.project_schemas import (
    GenerateProjectContentRequest,
    GenerateProjectContentResponse,
    TranslateProjectRequest,
    TranslateProjectResponse,
    ComponentResponse
)
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects/{project_id}/generate", response_model=GenerateProjectContentResponse)
async def generate_project_content(
    project_id: int,
    request: GenerateProjectContentRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: VertexAIClient = Depends(get_client)
):
    """
    Generate AI content for all components in a project
    
    - Uses project's brief, structure, and tone
    - Generates content for each component type (subject, body, cta, etc.)
    - Optionally uses uploaded images as context
    - Saves all generated content to database
    """
    
    # Get project with all relationships
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 1. Update project structure first if provided in the request
    # This ensures that new sections are persisted before we generate components for them
    if request.structure is not None:
        project.structure = request.structure
        db.add(project)
        db.flush()
        logger.info(f"Updated structure for project {project_id} before generation")

    # Determine image mapping for sections
    image_by_id = {img.id: img for img in project.images}
    
    # Use the current project structure (potentially updated above)
    project_structure = project.structure
    
    all_generated_components = []
    
    try:
        from app.api.generate import build_generation_prompt
        from app.models.schemas import StructureComponent, ComponentType
        import json
        
        # 2. First generate Header components (Subject & Pre-header)
        # These are usually project-wide, so we use the Main Brief
        header_structure = [
            StructureComponent(component=ComponentType.SUBJECT, count=1),
            StructureComponent(component=ComponentType.PRE_HEADER, count=1)
        ]
        
        header_prompt = build_generation_prompt(
            text=project.brief_text or "Create content",
            count=request.count,
            tone=project.tone or "professional",
            content_type="newsletter",
            structure=header_structure,
            context="Project Header"
        )
        
        logger.info(f"--- GENERATING HEADER for project {project_id} ---")
        header_response = await ai_client.generate_with_fixing(
            prompt=header_prompt,
            expected_variations=request.count,
            temperature=0.7,
            max_tokens=1024
        )
        
        try:
            header_data = json.loads(header_response)
            header_variations = header_data.get("variations", [])
            if header_variations:
                header_content = header_variations[0]
                logger.info(f"Header AI keys received: {list(header_content.keys())}")
                for key, value in header_content.items():
                    # Normalize key: remove any numeric suffix and convert to lowercase
                    # e.g., "Subject_1" -> "subject", "pre_header" -> "pre_header"
                    clean_key = key.lower().split("_")[0]
                    if key.lower().startswith("pre_header") or key.lower().startswith("preheader"):
                        clean_key = "pre_header"
                    
                    if clean_key in ["subject", "pre_header"]:
                        all_generated_components.append({
                            "component_type": clean_key,
                            "component_index": 1, # Headers always index 1
                            "generated_content": value,
                            "section_key": "header",
                            "section_order": -1
                        })
            else:
                logger.warning("No Variations found in Header response")
        except Exception as e:
            logger.error(f"Failed to process Header response: {str(e)}")

        # 3. Generate content for each section separately
        for section_idx, section in enumerate(project_structure):
            section_key = section.get("key", f"section_{section_idx}")
            section_name = section.get("name", f"Section {section_idx + 1}")
            
            # Use section-specific brief or fallback to project brief
            section_brief = section.get("brief")
            if not section_brief or not section_brief.strip():
                section_brief = project.brief_text or "Create content"
            
            # Use section-specific content type or default to newsletter
            section_content_type = section.get("content_type", "newsletter")
            
            # Get section-specific images
            section_image_ids = section.get("image_ids", [])
            section_images = [image_by_id[img_id] for img_id in section_image_ids if img_id in image_by_id]
            
            # Determine image URL for this section
            # STRICT: Only use images explicitly assigned to this section to avoid context contamination
            image_url = section_images[0].gcs_public_url if section_images else None
            
            # Prepare structure for this section (exclude images from text generation)
            # Group components by type to get correct counts for prompt
            allowed_types = []
            comp_counts = {}
            for comp_type in section.get("components", []):
                if comp_type == "image":
                    continue
                allowed_types.append(comp_type)
                comp_counts[comp_type] = comp_counts.get(comp_type, 0) + 1
            
            section_structure = []
            for comp_type, count in comp_counts.items():
                try:
                    comp_enum = ComponentType(comp_type)
                    section_structure.append(StructureComponent(component=comp_enum, count=count))
                except ValueError:
                    logger.warning(f"Invalid component type: {comp_type}")
                    continue
            
            if not section_structure:
                logger.info(f"No text components to generate for section {section_key}")
                continue

            # Build generation prompt for this section
            # Include has_image flag when an image is assigned to this section
            ai_prompt = build_generation_prompt(
                text=section_brief,
                count=request.count,
                tone=project.tone or "professional",
                content_type=section_content_type,
                structure=section_structure,
                context=f"Section: {section_name}" if section_name else None,
                has_image=bool(image_url)
            )
            
            logger.info(f"--- GENERATING SECTION: {section_name} (key: {section_key}) ---")
            
            # Generate content for this section
            response_text = await ai_client.generate_with_fixing(
                prompt=ai_prompt,
                expected_variations=request.count,
                temperature=0.7,
                max_tokens=2048,
                image_url=image_url
            )
            
            try:
                section_data = json.loads(response_text)
                variations = section_data.get("variations", [])
                
                if variations:
                    # Take the first variation
                    generated_content = variations[0]
                    logger.info(f"Section '{section_key}' AI keys received: {list(generated_content.keys())}")
                    
                    # DEBUG: Log actual content for each key to verify uniqueness
                    for k, v in generated_content.items():
                        logger.info(f"  {k}: {v[:80]}..." if len(str(v)) > 80 else f"  {k}: {v}")
                    
                    section_type_counters = {}
                    # Sort keys to ensure deterministic processing (important for index assignment)
                    sorted_keys = sorted(generated_content.keys())
                    
                    # Add each component to the list to be saved
                    for key in sorted_keys:
                        value = generated_content[key]
                        
                        # Handle base component type (e.g. "pre_header_1" -> "pre_header")
                        # We use rsplit to only split at the last underscore if it's followed by a number
                        base_type = None
                        if "_" in key:
                            parts = key.rsplit("_", 1)
                            if parts[1].isdigit():
                                base_type = parts[0]
                            else:
                                base_type = key
                        else:
                            base_type = key
                        
                        # STRICT FILTER: Only process components that were requested for this section
                        if base_type not in allowed_types:
                            continue
                            
                        # Increment local counter for this type in this section
                        section_type_counters[base_type] = section_type_counters.get(base_type, 0) + 1
                        current_index = section_type_counters[base_type]
                        
                        # Additional check: don't exceed requested count
                        if current_index > comp_counts.get(base_type, 0):
                            continue

                        # Create component data
                        logger.info(f"  -> Saving {base_type}_{current_index} for section {section_key}")
                        all_generated_components.append({
                            "component_type": base_type,
                            "component_index": current_index,
                            "generated_content": value,
                            "section_key": section_key,
                            "section_order": section_idx
                        })
                else:
                    logger.warning(f"No variations returned for section {section_key}")
            except Exception as e:
                logger.error(f"Failed to parse section {section_key} response: {str(e)}")
        
        # Save all generated components using the service (handles upsert/cleanup)
        saved_components = ProjectService.save_generated_content(
            db, project_id, user_id, None, all_generated_components
        )
        
        logger.info(f"Generated and saved {len(saved_components)} components across {len(project.structure)} sections for project {project_id}")
        
        # Send Slack notification (non-blocking)
        from app.utils.notifications import notify_generation_completed
        asyncio.create_task(
            notify_generation_completed(
                project_name=project.name,
                project_id=project.id,
                component_count=len(saved_components),
                user_email=user_id  # user_id is a string identifier
            )
        )
        
        return GenerateProjectContentResponse(
            project_id=project_id,
            components=[ComponentResponse.from_orm(c) for c in saved_components]
        )
        
    except Exception as e:
        logger.error(f"Error generating project content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.post("/projects/{project_id}/translate", response_model=TranslateProjectResponse)
async def translate_project_content(
    project_id: int,
    request: TranslateProjectRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: VertexAIClient = Depends(get_client)
):
    """
    Translate all components in a project to target languages
    
    - Uses project's target languages if not specified in request
    - Translates each component's generated content
    - Saves all translations to database
    """
    
    # Get project
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Determine target languages
    target_languages = request.languages or project.target_languages
    if not target_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No target languages specified"
        )
    
    # Get all components for this project
    components = db.query(Component).filter(
        Component.project_id == project_id
    ).all()
    
    if not components:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No components to translate. Generate content first."
        )
    
    try:
        # Translate each component for each language
        for component in components:
            if not component.generated_content:
                continue
            
            for lang_code in target_languages:
                # Call translation API
                from app.api.translate import translate_text_content
                
                translated_text = await translate_text_content(
                    text=component.generated_content,
                    target_language=lang_code.upper(),
                    source_language="EN",
                    ai_client=ai_client
                )
                
                # Save translation
                ProjectService.add_translation(
                    db=db,
                    component_id=component.id,
                    user_id=user_id,
                    language_code=lang_code,
                    translated_content=translated_text
                )
        
        # Refresh components to get translations
        db.refresh(project)
        updated_components = db.query(Component).filter(
            Component.project_id == project_id
        ).all()
        
        logger.info(f"Translated {len(components)} components for project {project_id}")
        
        # Send Slack notification (non-blocking)
        from app.utils.notifications import notify_translation_completed
        asyncio.create_task(
            notify_translation_completed(
                project_name=project.name,
                project_id=project.id,
                language_count=len(target_languages),
                component_count=len(components),
                user_email=user_id  # user_id is a string identifier
            )
        )
        
        return TranslateProjectResponse(
            project_id=project_id,
            components=[ComponentResponse.from_orm(c) for c in updated_components]
        )
        
    except Exception as e:
        logger.error(f"Error translating project content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate content: {str(e)}"
        )

