"""
Notification utilities for Mosaico
Sends notifications to Slack for important events
"""
import httpx
import logging
from datetime import datetime
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_slack_notification(
    message: str,
    project_name: Optional[str] = None,
    user_email: Optional[str] = None,
    event_type: str = "info"
) -> bool:
    """
    Send a notification to Slack webhook
    
    Args:
        message: Main notification message
        project_name: Name of the project (if applicable)
        user_email: Email of the user who triggered the action
        event_type: Type of event (info, success, error)
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook URL not configured, skipping notification")
        return False
    
    try:
        # Choose emoji based on event type
        emoji_map = {
            "info": ":information_source:",
            "success": ":white_check_mark:",
            "error": ":x:",
            "project": ":file_folder:",
            "generation": ":sparkles:",
            "translation": ":globe_with_meridians:"
        }
        emoji = emoji_map.get(event_type, ":bell:")
        
        # Build message blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{message}*"
                }
            }
        ]
        
        # Add context if available
        context_elements = []
        if project_name:
            context_elements.append(f"*Project:* {project_name}")
        if user_email:
            context_elements.append(f"*User:* {user_email}")
        context_elements.append(f"*Time:* <!date^{int(datetime.now().timestamp())}^{{date_short_pretty}} at {{time}}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}>")
        
        if context_elements:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": " | ".join(context_elements)
                    }
                ]
            })
        
        payload = {"blocks": blocks}
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.slack_webhook_url,
                json=payload
            )
            response.raise_for_status()
            
        logger.info(f"Slack notification sent: {message}")
        return True
        
    except httpx.HTTPError as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {str(e)}")
        return False


async def notify_project_created(project_name: str, user_email: Optional[str] = None):
    """Notify when a new project is created"""
    await send_slack_notification(
        message=f"New project created: {project_name}",
        project_name=project_name,
        user_email=user_email,
        event_type="project"
    )


async def notify_project_updated(project_name: str, user_email: Optional[str] = None):
    """Notify when a project is updated"""
    await send_slack_notification(
        message=f"Project updated: {project_name}",
        project_name=project_name,
        user_email=user_email,
        event_type="project"
    )


async def notify_generation_completed(
    project_name: str,
    component_count: int,
    user_email: Optional[str] = None
):
    """Notify when content generation is completed"""
    await send_slack_notification(
        message=f"Content generated: {component_count} component(s)",
        project_name=project_name,
        user_email=user_email,
        event_type="generation"
    )


async def notify_translation_completed(
    project_name: str,
    language_count: int,
    component_count: int,
    user_email: Optional[str] = None
):
    """Notify when translation is completed"""
    await send_slack_notification(
        message=f"Translation completed: {component_count} component(s) to {language_count} language(s)",
        project_name=project_name,
        user_email=user_email,
        event_type="translation"
    )

