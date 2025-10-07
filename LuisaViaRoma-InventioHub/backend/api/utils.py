from django.conf import settings
from api.models import ContentType, Language, LLMService, LLMModel, CONTENT_TYPES, LANGS
from django.utils.timezone import localtime
import boto3
import langcodes
import os

''' usage
    >python manage.py shell
    >from api.utils import init_db
    >init_db()
'''
def init_db():
    # populate DB with default content_type 
    for _, ctype_label in CONTENT_TYPES:
        ContentType.objects.get_or_create(name=ctype_label)

    # populate DB with default languages
    for lang_name, lang_code, country_code in LANGS:
        Language.objects.get_or_create(
            name = lang_name,
            lang_alpha2 = lang_code,
            country_alpha2 = country_code
    )
    
    # populate DB with default LLMs providers and models
    models_list = [
        "openai:gpt-4o",
        "openai:gpt-4o-mini",
        "openai:gpt-4.1",
        "openai:gpt-4.1-mini",
        "openai:o1-2024-12-17",
        "openai:o3-2025-04-16",
        "openai:o4-mini-2025-04-16",
        "google_genai:gemini-2.5-pro",
        "google_genai:gemini-2.5-flash",
        "google_genai:gemini-2.0-flash",
        "google_genai:gemini-2.0-flash-lite",
        "google_genai:gemini-1.5-pro",
        "google_genai:gemini-1.5-flash",
        "anthropic:claude-opus-4-20250514",
        "anthropic:claude-sonnet-4-20250514",
        "anthropic:claude-3-7-sonnet-latest",
        "anthropic:claude-3-5-sonnet-latest",
        "anthropic:claude-3-5-haiku-latest",
        "groq:deepseek-r1-distill-llama-70b",
        "groq:qwen/qwen3-32b",
        "groq:llama-3.3-70b-versatile"
    ]
    
    created_services = 0
    created_models = 0
    for model_string in models_list:
        try:
            # Split service name and model name
            service_name, model_name = model_string.split(':', 1)
            # Get or create the LLMService
            service, service_created = LLMService.objects.get_or_create(
                name=service_name,
                defaults={
                    'multimodal': True
                }
            )
            
            if service_created:
                created_services += 1
                print(f"Created service: {service_name}")
            
            # Create the LLMModel (use get_or_create to avoid duplicates)
            model, model_created = LLMModel.objects.get_or_create(
                service=service,
                model_id=model_name,
                defaults={
                    'name': model_name,
                    'api_key': '1',
                    'active': True
                }
            )
            
            if model_created:
                created_models += 1
                print(f"Created model: {service_name} - {model_name}")
            else:
                print(f"Model already exists: {service_name} - {model_name}")
                
        except ValueError:
            print(f"Invalid model string format: {model_string}")
        except Exception as e:
            print(f"Error processing {model_string}: {e}")
    
    print(f"Created {created_services} new services")
    print(f"Created {created_models} new models")
    print("\nDB initialized")

def file_upload_to_s3(file_path, objectName):
    s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    try:
        response = s3.upload_fileobj(file_path, settings.AWS_S3_BUCKET_NAME, objectName)
        return True 
    except Exception as e:
        print(e)
        return False

def delete_s3_file(object_key):
    s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    try:
        s3.delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=object_key)
        return True
    except Exception as e:
        print(f"S3 delete error: {e}")
        return False

def delete_s3_folder(user_id, content_id):
    """
    Delete all objects with the specified prefix (simulating folder deletion)
    For example: delete_s3_folder(4, 270) will delete all files in the "folder" 4/270/
    """

    s3 = boto3.client("s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    try:
        prefix = f"{user_id}/{content_id}/"
        # List all objects with the given prefix
        response = s3.list_objects_v2(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        # Check if any objects were found
        if 'Contents' not in response:
            print(f"No objects found with prefix: {prefix}")
            return True
        
        # Prepare objects for batch deletion
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
        # Delete objects in batches (max 1000 per batch)
        while objects_to_delete:
            batch = objects_to_delete[:1000]  # S3 limit is 1000 objects per delete request
            objects_to_delete = objects_to_delete[1000:]
            
            delete_response = s3.delete_objects(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Delete={'Objects': batch}
            )
            
            # Check for errors in deletion
            if 'Errors' in delete_response:
                for error in delete_response['Errors']:
                    print(f"Error deleting {error['Key']}: {error['Message']}")
            
            # Print successful deletions
            if 'Deleted' in delete_response:
                print(f"Successfully deleted {len(delete_response['Deleted'])} objects")
        
        return True
        
    except Exception as e:
        print(f"S3 folder delete error: {e}")
        return False

def stream_s3_file(request, user_id, content_id, file, file_name):
    from botocore.exceptions import ClientError
    from django.http import StreamingHttpResponse
    from rest_framework.response import Response
    from urllib.parse import quote

    s3_client = boto3.client('s3')
    try:
        file_key = f"{user_id}/{content_id}/{file}"
        s3_response = s3_client.get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=file_key)
    except s3_client.exceptions.NoSuchKey:
        return Response({"error": f"file {file_key} not found on s3 server"}, status=404)
    except ClientError as e:
        # più robusto: gestisce anche permessi, ecc.
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            return Response({"error": f"file {file_key} not found on s3 server"}, status=404)
        return Response({"error": "s3 error", "details": str(e)}, status=500)

    # ricava solo il nome base (senza eventuali slash) e quotalo per l'header
    basename = file_name.split("/")[-1]
    quoted = quote(basename)

    response = StreamingHttpResponse(
        s3_response["Body"].iter_chunks(),
        content_type=s3_response.get("ContentType", "application/octet-stream"),
    )
    response["Content-Length"] = str(s3_response.get("ContentLength", ""))
    # Header con supporto UTF-8 e fallback
    response["Content-Disposition"] = (
        f'attachment; filename="{basename}"; filename*=UTF-8\'\'{quoted}'
    )
    return response

def get_s3_file_base64(file_key):
    import base64
    s3_client = boto3.client('s3')
    try:
        s3_response = s3_client.get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=file_key)
        file_content = s3_response['Body'].read()
        base64_encoded = base64.b64encode(file_content).decode('utf-8')
        '''
        decoded_bytes = base64.b64decode(base64_encoded)
        decoded_text = decoded_bytes.decode('utf-8')
        print(f"{base64_encoded} -> Decoded: {decoded_text}")
        '''
        return base64_encoded
    except s3_client.exceptions.NoSuchKey:
        return None

def error_message(message):
    return {"error": message}

def print_connections():
    from django.db import connection
    import pprint
    pprint.pprint(connection.queries)
    print(f"queries-> {len(connection.queries)}")

def get_alpha2_from_name(language_name: str) -> str:
    try:
        lang = langcodes.find(language_name)
        return lang.language  # returns the ISO 639-1 (alpha2) code
    except LookupError:
        return language_name 

ALLOWED_EXTENTIONS = ('.jpg','.jpeg','.png','.webp','.txt','.pdf','.docx','.md')
def isAllowedFiles(files):
    # Allowed MIME types and extensions
    #allowed_types = ['image/png', 'application/pdf']
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        #if f.content_type not in allowed_types or ext not in allowed_extensions:
        if ext not in ALLOWED_EXTENTIONS:
            return False, f.name
    return True, None

def get_trans_task_data(translations):
    grouped = {}
    for t in translations:
        content_id = t.content_id
        translation_data = {
            "id": t.id,
            "state": t.state,
            "state_message": t.state_message,
            "language": {
                "name": t.language.name, 
                "lang_alpha2": t.language.lang_alpha2, 
                "country_alpha2": t.language.country_alpha2
            },
            "data": t.data,
        }

        if content_id not in grouped:
            grouped[content_id] = {
                "id": content_id,
                'title': t.content.title,
                'created_at': localtime(t.content.created_at).strftime(settings.DATETIME_FORMAT),
                'updated_at': localtime(t.content.updated_at).strftime(settings.DATETIME_FORMAT),
                'content_type': t.content.content_type.name,
                'state': t.content.state,
                #'sent_at': localtime(t.content.sent_at).strftime(settings.DATETIME_FORMAT) if t.content.sent_at else None,
                'sent_at': str(t.content.sent_at) if t.content.sent_at else None,
                'generated_at': str(t.content.generated_at) if t.content.generated_at else None,
                'status': t.content.status,
                'language': get_alpha2_from_name(t.content.language.name),
                'llm_name': f'{t.content.llmmodel.service.name.lower()}:{t.content.llmmodel.name.lower()}',
                'custom_prompt': t.content.custom_prompt,
                "data": t.content.data,
                's3files': t.content.s3files,
                "translations": []
            }

        grouped[content_id]["translations"].append(translation_data)

    response_data = list(grouped.values())
    return response_data
