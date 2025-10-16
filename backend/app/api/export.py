"""
Google Sheets Export API
"""
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from googleapiclient.discovery import build
from google.oauth2 import service_account

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.db.models import Project, Component, Translation
from app.models.project_schemas import ExportToSheetsRequest, ExportToSheetsResponse
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_spreadsheet_id(sheet_url: str) -> str:
    """Extract spreadsheet ID from Google Sheets URL"""
    # URL format: https://docs.google.com/spreadsheets/d/{ID}/edit...
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
    if not match:
        raise ValueError("Invalid Google Sheets URL")
    return match.group(1)


def get_sheets_service():
    """Get authenticated Google Sheets API service"""
    if not settings.google_sheets_credentials_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Sheets API not configured"
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            settings.google_sheets_credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Sheets API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to Google Sheets API"
        )


@router.post("/projects/{project_id}/export", response_model=ExportToSheetsResponse)
async def export_to_sheets(
    project_id: int,
    request: ExportToSheetsRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export project content to Google Sheets
    
    Replicates the familiar team structure:
    | ELEMENTS | EN | URLS | IT | FR | ... |
    """
    
    # Get project with all data
    project = ProjectService.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all components with translations
    components = db.query(Component).filter(
        Component.project_id == project_id
    ).order_by(Component.component_type, Component.component_index).all()
    
    if not components:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content to export. Generate content first."
        )
    
    try:
        # Extract spreadsheet ID
        spreadsheet_id = extract_spreadsheet_id(request.sheet_url)
        
        # Get Sheets service
        service = get_sheets_service()
        
        # Build data to write
        # Header row
        header = ["ELEMENTS", "EN (Original)", "URLS"]
        
        # Add language columns
        for lang in project.target_languages:
            header.append(lang.upper())
        
        # Data rows
        rows = [header]
        
        # Add project name as a section header
        rows.append([f"=== {project.name} ==="])
        rows.append([])  # Empty row
        
        # Component type mapping to display names
        component_display_names = {
            "subject": "SUBJECT",
            "pre_header": "PreHeader",
            "title": "TITLE",
            "body": "BODYCOPY",
            "cta": "CTA",
            "image": "IMG-"
        }
        
        # Add each component
        for component in components:
            # Determine display name
            type_name = component_display_names.get(component.component_type, component.component_type.upper())
            if component.component_index:
                element_name = f"{type_name} {component.component_index}"
            else:
                element_name = type_name
            
            row = [
                element_name,
                component.generated_content or "",
                component.component_url or ""
            ]
            
            # Add translations in order
            for lang in project.target_languages:
                translation = next(
                    (t for t in component.translations if t.language_code == lang),
                    None
                )
                row.append(translation.translated_content if translation else "")
            
            rows.append(row)
        
        # Determine where to write
        if request.export_mode == "new_sheet":
            # Create a new sheet with project name
            sheet_title = f"{project.name}_{project_id}"
            try:
                # Add new sheet
                add_sheet_request = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_title
                            }
                        }
                    }]
                }
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=add_sheet_request
                ).execute()
                range_name = f"'{sheet_title}'!A1"
            except Exception as e:
                logger.warning(f"Failed to create new sheet: {str(e)}")
                # Fallback to first sheet
                range_name = "A1"
        else:
            # Append to existing sheet
            range_name = "A1"
        
        # Write data
        body = {
            'values': rows
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        logger.info(f"Exported project {project_id} to Google Sheets")
        
        return ExportToSheetsResponse(
            success=True,
            sheet_url=request.sheet_url,
            message=f"Successfully exported {len(components)} components"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting to sheets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}"
        )

