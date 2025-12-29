"""
Labels API Endpoints
CRUD operations for dynamic project labels
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, User
from app.db.session import get_db
from app.db.models import Label

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Schemas =====

class LabelCreate(BaseModel):
    """Request to create a new label"""
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="gray", max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)


class LabelUpdate(BaseModel):
    """Request to update a label"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class LabelResponse(BaseModel):
    """Label response"""
    id: int
    name: str
    color: str
    description: Optional[str]
    created_by_user_name: Optional[str]
    
    class Config:
        from_attributes = True


# ===== Endpoints =====

@router.get("/labels", response_model=List[LabelResponse])
async def list_labels(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all available labels
    Labels are shared across the organization
    """
    labels = db.query(Label).order_by(Label.name).all()
    return labels


@router.post("/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    label_data: LabelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new label
    Label names must be unique
    """
    # Check for duplicate name
    existing = db.query(Label).filter(Label.name == label_data.name.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Label '{label_data.name}' already exists"
        )
    
    label = Label(
        name=label_data.name.lower(),
        color=label_data.color,
        description=label_data.description,
        created_by_user_id=user.id,
        created_by_user_name=user.name
    )
    
    db.add(label)
    db.commit()
    db.refresh(label)
    
    logger.info(f"Created label: {label.name}")
    return label


@router.put("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    label_data: LabelUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing label
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    # Check for duplicate name if updating name
    if label_data.name and label_data.name.lower() != label.name:
        existing = db.query(Label).filter(Label.name == label_data.name.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label '{label_data.name}' already exists"
            )
        label.name = label_data.name.lower()
    
    if label_data.color is not None:
        label.color = label_data.color
    
    if label_data.description is not None:
        label.description = label_data.description
    
    db.commit()
    db.refresh(label)
    
    logger.info(f"Updated label: {label.name}")
    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a label
    Note: This doesn't remove the label from projects that use it
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    db.delete(label)
    db.commit()
    
    logger.info(f"Deleted label: ID {label_id}")
    return None

