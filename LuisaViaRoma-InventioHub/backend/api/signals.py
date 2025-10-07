from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Content
from .utils import delete_s3_folder

@receiver(pre_delete, sender=Content)
def delete_content_s3_files(sender, instance, **kwargs):
    """
    Signal handler to delete S3 files when a Content object is deleted.
    This runs automatically whenever a Content object is deleted,
    including through Django admin.
    """
    try:
        # Get the creator's pk and content id before deletion
        creator_pk = instance.creator.pk if instance.creator else None
        content_id = instance.id
        
        if creator_pk and content_id:
            folder_deletion = delete_s3_folder(creator_pk, content_id)
            if not folder_deletion:
                print(f"\nFailed to delete S3 folder for content {content_id}, user {creator_pk}\n", flush=True)
        else:
            print(f"Could not delete S3 files for content {content_id}: missing creator or content id", flush=True)
            
    except Exception as e:
        print(f"Error deleting S3 files for content {instance.id}: {str(e)}", flush=True)
        # Note: We don't raise the exception here to avoid blocking the deletion
        # You might want to implement a cleanup job for failed deletions
