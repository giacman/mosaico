"""
Project CRUD API Endpoints
Now with collaboration support - all users can access all projects
"""
import logging
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, User
from app.db.session import get_db
from app.models.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ActivityLogResponse,
    SaveGeneratedContentRequest
)
from app.services.project_service import ProjectService
from app.utils.notifications import notify_project_created, notify_content_ready_for_approval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request, # Moved to the beginning
    project_data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email campaign project
    All users can create projects
    """
    try:
        project = ProjectService.create_project(db, user.id, user.name, project_data)
        
        # Send Slack notification (non-blocking)
        asyncio.create_task(
            notify_project_created(
                project_name=project.name,
                user_email=getattr(user, 'email', None) or user.name
            )
        )
        
        return project
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service layer (e.g., 409 Conflict)
        raise e
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    request: Request, # Moved to the beginning
    skip: int = 0,
    limit: int = 100,
    content_type: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List ALL projects (shared across all users)
    Optionally filter by content_type (newsletter, push_notification)
    """
    try:
        projects = ProjectService.list_projects(db, skip, limit, content_type)
        return projects
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    request: Request, # Moved to after project_id
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID
    All authenticated users can view any project
    """
    project = ProjectService.get_project(db, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    request: Request, # Moved to after project_id
    project_data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a project
    All authenticated users can edit any project
    """
    project = ProjectService.update_project(db, project_id, user.id, user.name, project_data)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Send Slack notification when project is approved
    if project_data.status and str(project_data.status.value if hasattr(project_data.status, 'value') else project_data.status) == "approved":
        asyncio.create_task(
            notify_content_ready_for_approval(
                project_name=project.name,
                user_email=getattr(user, 'email', None) or user.name
            )
        )
    
    return project


@router.post("/projects/{project_id}/duplicate", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_project(
    project_id: int,
    request: Request, # Moved to after project_id
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate a project with all its components, translations, and images
    All authenticated users can duplicate any project
    """
    try:
        duplicated_project = ProjectService.duplicate_project(
            db, project_id, user.id, user.name
        )
        return duplicated_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate project: {str(e)}"
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    request: Request, # Moved to after project_id
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project
    All authenticated users can delete any project
    """
    success = ProjectService.delete_project(db, project_id, user.id, user.name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return None


@router.get("/activity", response_model=List[dict])
async def get_global_activity(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global activity log across all projects
    Shows actions by all users for team transparency and audit purposes.
    Supports pagination via limit/offset for loading full history.
    """
    logs = ProjectService.get_global_activity_log(db, limit, offset)
    return logs


@router.get("/projects/{project_id}/activity", response_model=List[ActivityLogResponse])
async def get_project_activity(
    project_id: int,
    request: Request, # Moved to after project_id
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity log for a project
    Shows who did what and when for collaboration transparency
    """
    # Verify project exists
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    logs = ProjectService.get_activity_log(db, project_id, limit)
    return logs


@router.post("/projects/{project_id}/components", response_model=ProjectResponse)
async def save_generated_content(
    project_id: int,
    request_data: SaveGeneratedContentRequest,
    request: Request, # Moved to after request_data
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save generated components and translations for a project
    This replaces all existing components
    """
    try:
        # Convert Pydantic models to dicts for service layer
        components_data = [comp.model_dump() for comp in request_data.components]
        
        # Save components
        saved_components = ProjectService.save_generated_content(
            db, project_id, user.id, user.name, components_data
        )
        
        # Return updated project with all components
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving generated content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save generated content: {str(e)}"
        )


@router.post("/projects/{project_id}/sections/{section_key}/to-push", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_push_from_section(
    project_id: int,
    section_key: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new Push Notification project from a newsletter section.
    
    Takes the brief and image from the specified section and creates
    a new push_notification project with default structure (title, body).
    """
    from app.models.project_schemas import ProjectCreate, ContentType
    
    # Get source project
    source_project = ProjectService.get_project(db, project_id)
    if not source_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source project not found"
        )
    
    # Find the section in the project structure
    section_data = None
    for section in source_project.structure:
        if section.get("key") == section_key:
            section_data = section
            break
    
    if not section_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section '{section_key}' not found in project"
        )
    
    # Build the brief for the push notification
    section_name = section_data.get("name", section_key)
    section_brief = section_data.get("brief", "")
    
    # Combine project brief with section brief
    push_brief = f"Create a push notification based on this newsletter section:\n\n"
    if source_project.brief_text:
        push_brief += f"Original campaign brief: {source_project.brief_text}\n\n"
    if section_brief:
        push_brief += f"Section brief: {section_brief}\n"
    
    # Create the push notification project
    push_project_data = ProjectCreate(
        name=f"Push: {source_project.name} - {section_name}",
        brief_text=push_brief,
        structure=[],  # Will use default push structure
        tone=source_project.tone,
        target_languages=source_project.target_languages or [],
        labels=source_project.labels or [],
        content_type=ContentType.push_notification
    )
    
    push_project = ProjectService.create_project(db, user.id, user.name, push_project_data)
    
    # Log the transformation
    ProjectService._log_activity(
        db, push_project.id, user.id, user.name,
        "created_from_newsletter",
        "source_project_id", None, str(project_id)
    )
    db.commit()
    
    # Refresh and return
    db.refresh(push_project)
    return push_project
