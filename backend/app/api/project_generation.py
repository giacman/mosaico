"""
Project-based Generation and Translation Endpoints
Combines AI generation with database persistence
"""
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
    Generate AI content for all components in a project with section-level briefs.
    
    - Supports section-specific briefs (falls back to project.brief_text)
    - Supports section-specific images
    - Generates content per section with appropriate context
    - Saves all generated content to database with section_key tracking
    """
    
    # Get project with all relationships
    project = ProjectService.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create image lookup by ID
    image_by_id = {img.id: img for img in project.images}
    
    all_components = []
    
    try:
        from app.api.generate import build_generation_prompt
        import json
        
        # Generate content for each section separately
        for section_idx, section in enumerate(project.structure):
            section_key = section.get("key", f"section_{section_idx}")
            section_name = section.get("name", f"Section {section_idx + 1}")
            
            # Use section-specific brief or fallback to project brief
            section_brief = section.get("brief") or project.brief_text or "Create content"
            
            # Use section-specific content type or default to newsletter
            section_content_type = section.get("content_type", "newsletter")
            
            # Get section-specific images
            section_image_ids = section.get("image_ids", [])
            section_images = [image_by_id[img_id] for img_id in section_image_ids if img_id in image_by_id]
            
            # Determine image URL for this section
            image_url = None
            if section_images:
                image_url = section_images[0].gcs_public_url
            elif not section_image_ids and project.images:
                # Fallback to project images if section has no specific images
                image_url = project.images[0].gcs_public_url
            
            # Prepare structure for this section
            section_structure = []
            for comp_type in section.get("components", []):
                section_structure.append({
                    "component": comp_type,
                    "count": 1  # Each component appears once per section
                })
            
            # Build generation prompt for this section
            ai_prompt = build_generation_prompt(
                text=section_brief,
                count=request.count,
                tone=project.tone or "professional",
                content_type=section_content_type,
                structure=section_structure,
                context=f"Section: {section_name}" if section_name else None
            )
            
            logger.info(
                f"Generating content for section '{section_name}' (key: {section_key}) "
                f"with {len(section_structure)} components"
            )
            
            # Generate content for this section
            response_text = await ai_client.generate_with_fixing(
                prompt=ai_prompt,
                expected_variations=request.count,
                temperature=0.7,
                max_tokens=2048,
                image_url=image_url
            )
            
            variations = json.loads(response_text).get("variations", [])
            
            if not variations:
                logger.warning(f"No content generated for section {section_key}")
                continue
            
            # Take the first variation
            generated_content = variations[0]
            
            # Save each component with section_key
            for comp_idx, (key, value) in enumerate(generated_content.items()):
                # Parse component type and index
                if "_" in key:
                    parts = key.rsplit("_", 1)
                    component_type = parts[0]
                    component_index = int(parts[1])
                else:
                    component_type = key
                    component_index = comp_idx
                
                # Create component with section tracking
                component = Component(
                    project_id=project_id,
                    section_key=section_key,
                    section_order=section_idx,
                    component_type=component_type,
                    component_index=component_index,
                    generated_content=value
                )
                db.add(component)
                all_components.append(component)
        
        db.commit()
        
        # Refresh to get IDs
        for comp in all_components:
            db.refresh(comp)
        
        logger.info(
            f"Generated and saved {len(all_components)} components across "
            f"{len(project.structure)} sections for project {project_id}"
        )
        
        return GenerateProjectContentResponse(
            project_id=project_id,
            components=[ComponentResponse.from_orm(c) for c in all_components]
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
    project = ProjectService.get_project(db, project_id, user_id)
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

