"""
File Upload API Endpoints
"""
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from google.cloud import storage

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.db.models import Image, Project
from app.models.project_schemas import ImageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed image MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload-image", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image file to Google Cloud Storage
    
    - Validates file type and size
    - Uploads to GCS bucket
    - Saves metadata to database
    - Returns image ID and public URL
    """
    
    # Verify project exists (all authenticated users can upload to any project)
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file"
        )
    
    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    gcs_path = f"projects/{project_id}/{unique_filename}"
    
    try:
        # Upload to Google Cloud Storage
        storage_client = storage.Client(project=settings.gcp_project_id)
        bucket = storage_client.bucket(settings.gcs_bucket_images)
        blob = bucket.blob(gcs_path)
        
        # Upload with content type
        blob.upload_from_string(
            file_content,
            content_type=file.content_type
        )
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        logger.info(f"Uploaded image to GCS: {gcs_path}")
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )
    
    # Save metadata to database
    try:
        image = Image(
            project_id=project_id,
            user_id=user_id,
            filename=file.filename,
            gcs_path=f"gs://{settings.gcs_bucket_images}/{gcs_path}",
            gcs_public_url=public_url
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        logger.info(f"Saved image metadata: ID {image.id}")
        
        return image
        
    except Exception as e:
        logger.error(f"Error saving image metadata: {str(e)}")
        # Try to clean up the uploaded file
        try:
            blob.delete()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image metadata"
        )


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get image metadata by ID
    """
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == user_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return image


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an image (from DB and GCS)
    """
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == user_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete from GCS
    try:
        storage_client = storage.Client(project=settings.gcp_project_id)
        bucket = storage_client.bucket(settings.gcs_bucket_images)
        # Extract blob name from gcs_path
        blob_name = image.gcs_path.replace(f"gs://{settings.gcs_bucket_images}/", "")
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Deleted image from GCS: {blob_name}")
    except Exception as e:
        logger.warning(f"Failed to delete image from GCS: {str(e)}")
        # Continue with DB deletion even if GCS deletion fails
    
    # Delete from database
    db.delete(image)
    db.commit()
    
    logger.info(f"Deleted image: ID {image_id}")
    return None

