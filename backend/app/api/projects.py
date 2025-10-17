"""
Project CRUD API Endpoints
Now with collaboration support - all users can access all projects
"""
import logging
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, User
from app.db.session import get_db
from app.models.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ActivityLogResponse
)
from app.services.project_service import ProjectService
from app.utils.notifications import notify_project_created, notify_project_updated

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
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
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List ALL projects (shared across all users)
    """
    try:
        projects = ProjectService.list_projects(db, skip, limit)
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
    
    # Send Slack notification (non-blocking)
    asyncio.create_task(
        notify_project_updated(
            project_name=project.name,
            user_email=getattr(user, 'email', None) or user.name
        )
    )
    
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
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


@router.get("/projects/{project_id}/activity", response_model=List[ActivityLogResponse])
async def get_project_activity(
    project_id: int,
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
