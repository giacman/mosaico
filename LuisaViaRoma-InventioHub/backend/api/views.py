from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from rest_framework.response import Response
from .models import Role, Content, ContentFile, ContentType, \
    Language, LangTranslation, LLMService, LLMModel, Notification, CONTENT_STATES, CONTENT_STATUSES
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from django.db.models import Case, When, Value, IntegerField, Prefetch, Q
from .utils import error_message, print_connections, \
    file_upload_to_s3, delete_s3_file, stream_s3_file, get_s3_file_base64, \
    ALLOWED_EXTENTIONS, isAllowedFiles, get_trans_task_data
from .GSheetBuilder import GSheetBuilder
import csv
import json
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.db.models import OuterRef, Exists
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth import get_user_model
from datetime import datetime


class IsAuth(IsAuthenticated):
    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return super().has_permission(request, view)


class RolePermission(BasePermission):
    roles = None  # Can be a string or list

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        if not request.user.is_authenticated:
            return False
        # Support both single role and list of roles
        if isinstance(self.roles, str):
            return request.user.role == self.roles
        if isinstance(self.roles, list):
            return request.user.role in self.roles
        return False


class IsAdmin(RolePermission):
    roles = 'amministratore'


class IsCopywriter(RolePermission):
    roles = 'copywriter'


class IsApprovatore(RolePermission):
    roles = 'approvatore'


class IsTraduttore(RolePermission):
    roles = 'traduttore'


class IsPublisher(RolePermission):
    roles = 'publisher'


class IsCopywriterOrPublisher(RolePermission):
    roles = ['copywriter', 'publisher']


class IsCopywriterOrApprovatore(RolePermission):
    roles = ['copywriter', 'approvatore']


class IsCopywriterOrAdmin(RolePermission):
    roles = ['copywriter', 'amministratore']


class IsApprovatoreOrTraduttore(RolePermission):
    roles = ['approvatore', 'traduttore']


class AuthTask(BasePermission):
    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return auth_task(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get("access_token")
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID)
        email = idinfo.get("email")
        given_name = idinfo.get("given_name")
        family_name = idinfo.get("family_name")

        User = get_user_model()
        user, _ = User.objects.get_or_create(email=email, defaults={
            "username": email,
            "first_name": given_name,
            "last_name": family_name
        })
        refresh = RefreshToken.for_user(user)

        response = Response({
            "access": str(refresh.access_token),
            # "refresh": str(refresh),
            'id': user.id,
            'username': getattr(user, 'username', None),
            'first_name': getattr(user, 'first_name', None),
            'last_name': getattr(user, 'last_name', None),
            'role': getattr(user, 'role', None),
            'roles': [
                {'value': role.name, 'label': role.get_name_display()}
                for role in getattr(user, 'roles', []).all()
            ] if getattr(user, 'roles', None) else [],

        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh',
            value=refresh,
            httponly=True,
            # secure = True, # usa solo se hai HTTPS
            secure=settings.SECURE_COOKIE,
            samesite='Lax',  # o 'None' se hai domini separati
            path='/api/login/refresh/',
            max_age=60 * 60 * 24 * 90  # 90 giorni
        )
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuth])
def logout(request):
    response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
    response.delete_cookie(
        key='refresh',
        path='/api/login/refresh/',
        samesite='Lax',
        secure=settings.SECURE_COOKIE
    )

    return response


class SyncRoles(APIView):
    permission_classes = [IsAuth]

    def post(self, request):
        """
        POST to /api/sync_roles/
        {
            "user_id": 5,
            "roles": ["admin", "editor"]
        }

        - Roles not in this list will be removed from user.roles.
        - Roles in this list and missing will be added.
        """
        user_id = request.data.get("user_id")
        role_names = request.data.get("roles", [])

        if not user_id or not isinstance(role_names, list):
            return Response(
                {"detail": "user_id and list of roles are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        # Get valid roles from DB
        desired_roles = Role.objects.filter(name__in=role_names)
        desired_names_set = set(desired_roles.values_list("name", flat=True))

        # Get current roles
        current_roles = user.roles.all()
        current_names_set = set(current_roles.values_list("name", flat=True))

        # Compute additions/removals
        to_add = desired_roles.exclude(name__in=current_names_set)
        to_remove = current_roles.exclude(name__in=desired_names_set)

        if to_add.exists():
            user.roles.add(*to_add)
        if to_remove.exists():
            user.roles.remove(*to_remove)

        user.save()

        return Response({
            "user": user.username,
            "synced_roles": list(desired_names_set),
            "added": [r.name for r in to_add],
            "removed": [r.name for r in to_remove],
            "message": "Roles synced successfully."
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuth])
def get_role(request):
    User = get_user_model()
    try:
        user = User.objects.get(pk=request.user.pk)
        return Response({
            "role": user.role,
            'roles': [role.get_name_display() for role in user.roles.all()],
        },
            status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(error_message('user not found'), status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuth])
def change_role(request):
    User = get_user_model()
    new_role = request.GET.get("new_role")
    if new_role:
        new_role = new_role.lower()
    else:
        return Response(error_message('Missing new_role paramater'), status=status.HTTP_403_FORBIDDEN)
    try:
        user = User.objects.get(pk=request.user.pk)
        ALLOWED_ROLES = [role.get_name_display().lower() for role in user.roles.all()]
        if new_role in ALLOWED_ROLES:
            user.role = new_role
            user.save()
            return Response({"role": user.role}, status=status.HTTP_200_OK)
        else:
            return Response(error_message('forbidden to change to this role'), status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        return Response(error_message('user not found'), status=status.HTTP_404_NOT_FOUND)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'role': self.user.role,
            'roles': [role.get_name_display() for role in self.user.roles.all()],
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get('refresh')
        response.set_cookie(
            key='refresh',
            value=refresh,
            httponly=True,
            # secure = True, # usa solo se hai HTTPS
            secure=settings.SECURE_COOKIE,
            samesite='Lax',  # o 'None' se hai domini separati
            path='/api/login/refresh/',
            max_age=60 * 60 * 24 * 90  # 90 giorni
        )
        return response


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None

    def validate(self, attrs):
        refresh_from_cookie = self.context['request'].COOKIES.get('refresh')
        # If not in cookie, check if it's in the request body
        refresh_from_body = attrs.get('refresh')
        # Use cookie token if available, otherwise use body token (Mobile devices etc.)
        if refresh_from_cookie:
            attrs['refresh'] = refresh_from_cookie
        elif refresh_from_body:
            # Keep the refresh token from the body as is
            pass
        else:
            raise serializers.ValidationError('No valid refresh token found in cookie or body')

        return super().validate(attrs)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LangTranslationSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()

    # id = serializers.IntegerField()
    class Meta:
        model = LangTranslation
        fields = "__all__"


class LLMProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMService
        fields = "__all__"


class LLMModelSerializer(serializers.ModelSerializer):
    # service_name = serializers.CharField(source='service.name', read_only=True)
    provider = LLMProviderSerializer(read_only=True, source="service")

    class Meta:
        model = LLMModel
        exclude = ['api_key']
        read_only_fields = ['model_id', 'service', 'name']


class LLMServiceSerializer(serializers.ModelSerializer):
    models = LLMModelSerializer(many=True, read_only=True)

    class Meta:
        model = LLMService
        fields = ['name', 'models', 'multimodal']


class ContentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentFile
        fields = ['id', 'name', 'key']


class ContentSerializer(serializers.ModelSerializer):
    translations = LangTranslationSerializer(many=True, required=False)
    selected_llmmodel = LLMModelSerializer(read_only=True, source='llmmodel')

    class Meta:
        model = Content
        fields = ['creator', 'created_at', 'updated_at', 'state', 'state_message', 'sent_at', 'generated_at', 'status',
                  'rejection_message',
                  'content_type', 'title', 'llmmodel', 'selected_llmmodel',
                  'custom_prompt', 'language', 'schema', 'data', 'translations', 's3files'
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        request = self.context.get('request')
        if instance and request and request.method == 'PUT' and request.user.role == "copywriter":
            self.fields['creator'].read_only = True

    def create(self, validated_data):
        # only if sending to AI we need to convert the schema to Output 
        # if just saving the content we just keep the Input schema
        if validated_data.get('state') == 'sent':
            validated_data['schema'] = json.loads(get_output_schema_from_data(validated_data))
            validated_data['sent_at'] = datetime.now()
        # if state is not sent from the client or is sending local state it means we are just saving and
        # not sending to AI so the schema must stay as Input
        if validated_data.get("state") == None or validated_data.get("state") == "local":
            content_type = str(validated_data.get("content_type"))
            validated_data['schema'] = json.loads(get_input_schema(content_type))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # same as create
        if validated_data.get('state') == 'sent':
            if instance.state == "local":
                validated_data['schema'] = json.loads(get_output_schema_from_data(validated_data))
            validated_data['sent_at'] = datetime.now()
        # same as create but consider the current instance state
        if instance.state == "local" and (
                validated_data.get("state") == None or validated_data.get("state") == "local"):
            validated_data['schema'] = json.loads(get_input_schema(instance.content_type.name))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['content_type'] = instance.content_type.name
        rep['content_type_id'] = instance.content_type.id
        rep['language'] = LanguageSerializer(instance.language).data
        rep['llm_name'] = f'{instance.llmmodel.service.name.lower()}:{instance.llmmodel.name.lower()}'
        rep['sent_at'] = str(instance.sent_at) if instance.sent_at else None
        rep['generated_at'] = str(instance.generated_at) if instance.generated_at else None
        return rep


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'name']


@api_view(['POST'])
@permission_classes([IsCopywriter])
def create_content(request):
    files_to_upload = request.FILES.getlist('files')
    if files_to_upload:
        if len(files_to_upload) > 5:
            return Response(error_message("You can only upload up to 5 files"), status=403)

        is_valid, invalid_file = isAllowedFiles(files_to_upload)
        if not is_valid:
            return Response(
                error_message(f"Invalid file type: {invalid_file}. Only {ALLOWED_EXTENTIONS} files are allowed."),
                status=400)

    serializer = ContentSerializer(data=request.data)
    if serializer.is_valid():
        content = serializer.save()
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_files = upload_to_s3(content.id, request)
    if uploaded_files == None:
        content.delete()
        return Response(error_message("error on uploading to s3"), status=500)
    else:
        content.s3files = [
            {"name": file_data['name'], "key": file_data['key']}
            for file_data in uploaded_files
        ]
        content.save()

    if content.state == 'sent':
        requests.post(settings.AI_CORE_URL + '/generate/', json=serializer.data)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def get_content(request, pk):
    try:
        content = Content.objects.get(pk=pk)
    except Content.DoesNotExist:
        return Response(error_message('content not found'), status=status.HTTP_404_NOT_FOUND)

    all_languages = list(Language.objects.all())
    serializer = ContentSerializer(content, context={'all_languages': all_languages})
    return Response(serializer.data)


class ContentHistorySerializer(serializers.ModelSerializer):
    history_date = serializers.DateTimeField()
    history_user = serializers.StringRelatedField()
    history_type = serializers.CharField()
    llmmodel = serializers.StringRelatedField()
    content_type = serializers.StringRelatedField()
    language = serializers.StringRelatedField()
    creator = serializers.StringRelatedField()

    class Meta:
        model = Content.history.model
        fields = '__all__'


@api_view(['GET'])
@permission_classes([IsCopywriter])
def get_content_history(request, pk):
    try:
        history_qs = Content.history.filter(
            id=pk,
            # creator=request.user,
            # history_user=request.user,
            # status__in=["bozza", "bozza_validata", "validata"]
        ).order_by('-history_date')

        if history_qs.count() < 2:
            return Response(error_message("Not enough history records to compare."), status=400)

        diffs = []

        import pytz
        for i in range(len(history_qs) - 1):
            newer = history_qs[i]
            older = history_qs[i + 1]
            delta = newer.diff_against(older)

            # continue if only the status field was changed - no other fields were modified
            if delta.changes and all(change.field == "status" for change in delta.changes):
                continue

            change_set = {
                "id": older.id,
                "history_id": older.history_id,
                "title": older.title,
                "from": older.history_date,
                # "to": newer.history_date.strftime("%d-%m-%Y %H:%M"),
                "to": newer.history_date.astimezone(pytz.timezone("Europe/Rome")).strftime("%d-%m-%Y %H:%M"),
                "changes": [],
            }

            for change in delta.changes:
                old_val = change.old
                new_val = change.new

                # if the val is a json (s3files) extract name only
                def get_name(val):
                    if isinstance(val, list):
                        return [item.get("name") for item in val if isinstance(item, dict) and "name" in item]
                    return val

                old_val = get_name(old_val)
                new_val = get_name(new_val)

                change_set["changes"].append({
                    "field": change.field,
                    "old": old_val,
                    "new": new_val
                })

            # Only include entries with actual diffs and exclude the last change, 
            # which represents the current draft state.
            # if change_set["changes"] and i > 1:
            if change_set["changes"]:
                diffs.append(change_set)

        return Response({"diffs": diffs})

    except Content.DoesNotExist:
        return Response({"detail": "Content not found."}, status=404)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsCopywriter])
def update_content(request, pk):
    try:
        content = Content.objects.get(pk=pk)
    except Content.DoesNotExist:
        return Response({'error': 'Content not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        if content.status in ("bozza", "bozza_validata", "bozza_rifiutata", "review_traduzioni"):
            # if we are in translation review we have to wait a complete validation to delte the draft in translation review
            if content.status == "review_traduzioni":
                languages = LangTranslation.objects.filter(content=content.id).all()
                for lang in languages:
                    if lang.status != "validata":
                        return Response(error_message("there is a translation currently in pending"),
                                        status=status.HTTP_403_FORBIDDEN)
            content_id = content.id
            content.delete()
            return Response({'id': content_id}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "you can only delete a draft, valid or a rejected, or in review translations"},
                status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        uploaded_files = []
        new_status = request.data.get("status")

        # if request.user.role == "copywriter" and new_status == None and content.status == 'bozza':
        if request.user.role == "copywriter" and new_status == None:
            existing_files = content.s3files if isinstance(content.s3files, list) else []
            files_to_upload = request.FILES.getlist('files')
            if files_to_upload:
                if len(existing_files) + len(files_to_upload) > 5:
                    return Response(error_message("You can only upload up to 5 files"), status=403)
                is_valid, invalid_file = isAllowedFiles(files_to_upload)
                if not is_valid:
                    return Response(error_message(f"Invalid file type: {invalid_file}. \
                                    Only {ALLOWED_EXTENTIONS} files are allowed."), status=400)

                uploaded_files = upload_to_s3(content.id, request)
                if uploaded_files == None:
                    return Response(error_message("error on uploading to s3"), status=500)
                else:
                    new_files = [{"name": file_data['name'], "key": file_data['key']} for file_data in uploaded_files]
                    combined_files = existing_files + new_files
                    content.s3files = combined_files
                    content.save(update_fields=["s3files"])

        if request.user.role == "copywriter" and new_status:
            # se una review è stata rifiutata, il copywriter può solo rimettere lo stato in review 
            if content.status == "bozza_rifiutata" and new_status != 'review':
                return Response(status=status.HTTP_403_FORBIDDEN)

            # se la bozza è validata, il copywriter può solo mandarla in review_traduzioni o validata
            if content.status == "bozza_validata" and new_status != "review_traduzioni" and new_status != "validata":
                return Response(status=status.HTTP_403_FORBIDDEN)
            # se la manda come validata, controllo che effettivamente non ci siano traduzioni da validare
            if content.status == "bozza_validata" and new_status == "validata":
                trans = LangTranslation.objects.filter(content=content.id).all()
                if len(trans) > 0:
                    return Response({"Error": 'you have translations to validate'}, status=status.HTTP_403_FORBIDDEN)

            # se in review_traduzioni la si può cambiare su validata solo se tutte le traduzioni 
            # sono state validate, altrimenti lo status rimane su review_traduzioni 
            if content.status == "review_traduzioni" and new_status == "validata":
                languages = LangTranslation.objects.filter(content=content.id).all()
                for lang in languages:
                    if lang.status != "validata":
                        return Response(status=status.HTTP_403_FORBIDDEN)

            if content.status == "review_traduzioni" and new_status != "validata":
                return Response(status=status.HTTP_403_FORBIDDEN)

        all_languages = list(Language.objects.all())
        serializer = ContentSerializer(content, data=request.data,
                                       context={'all_languages': all_languages, 'request': request})
        if serializer.is_valid():
            content = serializer.save()
            if content.state == 'sent':
                payload = serializer.data
                requests.post(settings.AI_CORE_URL + '/generate/', json=payload)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(error_message("bad request"), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def send_to_content_review(request, pk):
    try:
        content = Content.objects.get(pk=pk)
    except Exception as e:
        return Response(error_message(f"Content not found: {e}"), status=status.HTTP_404_NOT_FOUND)
    if content.state != "local":
        content.status = "review"
        content.set_updated_by(request.user)
        content.save()
        return Response({'detail': f"{content.id} in review"}, status=status.HTTP_200_OK)
    else:
        return Response(error_message("you can't send in review if you are not passed through AI"),
                        status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def send_to_final_review(request, pk):
    content = get_object_or_404(Content, pk=pk)
    # TODO fare i check
    # if content.status != "review_traduzioni":
    content.status = "validata"
    content.set_updated_by(request.user)
    content.save()
    return Response({'detail': f"{content.id} validata"}, status=status.HTTP_200_OK)
    # else:
    #     return Response(error_message("you can't send in final review without translations"),
    #                     status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def send_to_ai(request, pk):
    try:
        content = Content.objects.get(pk=pk)
    except Exception as e:
        return Response(error_message(f"Content not found: {e}"), status=status.HTTP_404_NOT_FOUND)
    if content.status == "bozza" or content.status == "bozza_validata" or content.status == "bozza_rifiutata":
        content.state = "sent"
        content.save()
        all_languages = list(Language.objects.all())
        serializer = ContentSerializer(content, context={'all_languages': all_languages, 'request': request})
        if serializer.is_valid():
            payload = serializer.data
            requests.post(settings.AI_CORE_URL + '/generate/', json=payload)
        return Response({'detail': f"{content.id} sent to ai"}, status=status.HTTP_200_OK)
    else:
        return Response(error_message("forbidden"), status=status.HTTP_403_FORBIDDEN)


@api_view(['PUT'])
@permission_classes([IsCopywriter])
def send_in_review_translation(request):
    '''
    curl -X PUT http://localhost:8001/api/send_in_review_translation/ \
    -H "Content-Type: application/json" \
    -d '
          {
            "content_id": 205,
          }
    '
    '''
    payload = request.data
    content_id = payload.get('content_id')

    if not content_id:
        return Response(error_message("Content id not provided"), status=status.HTTP_404_NOT_FOUND)

    content = get_object_or_404(Content, id=content_id)
    content.status = "review_traduzioni"
    content.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def restore_content(request, content_id, history_id):
    try:
        content = Content.objects.get(id=content_id,
                                      status__in=["bozza", "bozza_validata", "bozza_rifiutata"],
                                      state__in=["local", "success", "failed"]
                                      )
        old_version = content.history.get(history_id=history_id)
    except Exception:
        return Response({"Error": "Not found or not allowed."}, status=status.HTTP_404_NOT_FOUND)

    '''
    # Get the previous version for diff comparison
    previous_version = content.history.filter(history_date__lt=old_version.history_date).order_by('-history_date').first()
    # If there's a previous version, check if the only diff is 'status'
    if previous_version:
        diff = old_version.diff_against(previous_version)
        changed_fields = [change.field for change in diff.changes]
        # If 'status' changed, don't allow restoring this version
        if 'status' in changed_fields:
            return Response(
                {"detail": "Cannot restore a version with only status change."},
                status=status.HTTP_400_BAD_REQUEST
            )
    '''

    restored = old_version.instance
    restored.pk = content.pk
    restored.history_user = request.user
    restored.save()
    serializer = ContentSerializer(restored)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_content_queryset():
    return Content.objects.select_related(
        'creator', 'content_type', 'language', 'llmmodel'
    ).prefetch_related(
        Prefetch(
            'translations',
            queryset=LangTranslation.objects.select_related('language')
        ),
    )


@api_view(['GET'])
@permission_classes([IsCopywriter])
def get_contents(request, filter=None):
    contents = get_content_queryset()
    contents = get_contents_filtered(request, contents)
    if filter == "review_traduzioni":
        rejected_translation_exists = LangTranslation.objects.filter(
            content=OuterRef('pk'),
            status='rifiutata'
        )
        contents = contents.filter(
            status__in=['review_traduzioni', 'bozza_validata']
        ).annotate(
            has_rejected_translation=Exists(rejected_translation_exists)
        ).order_by('-has_rejected_translation', '-created_at')

    if filter == None:
        contents = contents.filter(
            status__in=['bozza_rifiutata', 'bozza', 'review']  # 'bozza_validata',
        ).annotate(
            priorita_status=Case(
                When(status='bozza_rifiutata', then=Value(0)),
                When(status='bozza_validata', then=Value(1)),
                When(status='bozza', then=Value(2)),
                When(status='review', then=Value(3)),
                output_field=IntegerField()
            )
        ).order_by('priorita_status', '-created_at')

    all_languages = list(Language.objects.all())
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True, context={'all_languages': all_languages})
    return paginator.get_paginated_response(serializer.data)


def auth_task(request):
    token = request.headers.get('TaskToken')
    if not token:
        return False
    if token != settings.TASK_TOKEN:
        return False
    return True


@api_view(['GET'])
@permission_classes([AuthTask])
def get_generation_tasks(request):
    '''
    curl -X GET http://localhost:8000/api/get_generation_tasks/?state=sent -H "TaskToken:abc"
    '''
    state_filter = request.GET.get('state')
    if state_filter:
        contents = get_content_queryset().filter(state=state_filter)
    else:
        contents = get_content_queryset().filter(state="sent")
    serializer = ContentSerializer(contents, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AuthTask])
def update_generation_task(request):
    '''
    curl -X PUT http://localhost:8000/api/update_generation_task/ -H "TaskToken:abc" \
      -H "Content-Type: application/json" \
      -d '{
            "id": 280,
            "state": "success",
            "state_message": "my message"
            "data": {...}
          }'
    '''
    pk = request.data.get("id")
    if not pk:
        return Response({'detail': 'Missing "id" in request'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        content = Content.objects.get(pk=pk)
    except Exception:
        return Response({'detail': 'Content not found'}, status=status.HTTP_404_NOT_FOUND)

    if content.state != "sent" and content.state != "received" and content.state != "pending":
        return Response({'detail': f'the content {content.id} state is {content.state}, you can not modify'},
                        status=status.HTTP_403_FORBIDDEN)

    state = request.data.get("state")
    if not state:
        return Response({'detail': 'Missing "state" field in request'}, status=status.HTTP_400_BAD_REQUEST)
    ALLOWED_STATES = [state[0] for state in CONTENT_STATES if state[0] not in ('local', 'sent')]
    if state not in ALLOWED_STATES:
        return Response({'detail': f'Invalid state. Allowed values are: {ALLOWED_STATES}'},
                        status=status.HTTP_400_BAD_REQUEST)
    content.state = state

    state_message = request.data.get('state_message')
    if state_message:
        content.state_message = state_message

    data = request.data.get('data')
    if data:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return Response({'detail': 'Invalid JSON string in "data" field'}, status=status.HTTP_400_BAD_REQUEST)
        elif not isinstance(data, dict):
            return Response({'detail': '"data" must be a JSON object'}, status=status.HTTP_400_BAD_REQUEST)
        content.data = data
    content.generated_at = datetime.now()
    content.save()
    return Response({'id': content.id, 'detail': 'successfully updated'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AuthTask])
def get_trans_tasks(request):
    '''
    curl -X GET http://localhost:8000/api/get_trans_tasks/?state=sent -H "TaskToken:abc"
    '''
    state = request.GET.get('state')
    # If state is provided, use it; otherwise default to ['sent', 'pending']
    if state:
        states = [state.strip()]
    else:
        states = ["sent", "pending"]

    translations = LangTranslation.objects.filter(
        state__in=states,
        content__status='review_traduzioni',
        content__state='success'
    ).select_related('language', 'content', 'content__llmmodel', 'content__llmmodel__service')
    response_data = get_trans_task_data(translations)
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AuthTask])
def update_trans_tasks(request):
    '''
    curl -X PUT http://localhost:8000/api/update_trans_tasks/ -H "TaskToken:abc" \
    -H "Content-Type: application/json" \
    -d '
    [
      {
        "id": 286,
        "translations": [
          {
            "id": 205,
            "state": "success",
            "state_message": "my message",
            "data": {"translated_text": "Hola mundo"}
          },
          {
            "id": 206,
            "state": "success",
            "state_message": "my message",
            "data": {"translated_text": "Hello world"}
          }
        ]
      }
    ]
    '
    '''
    payload = request.data  # Expecting a list of content dicts with translations inside
    translations_to_update = []
    updated = []
    errors = []
    content_id = None

    for content in payload:
        translations = content.get('translations', [])
        content_id = content.get('id')

        for trans in translations:
            trans_id = trans.get('id')
            new_state = trans.get('state')
            new_state_message = trans.get('state_message')
            new_data = trans.get('data')

            if not trans_id:
                errors.append({"detail": "Missing translation id", "translation": trans})
                continue

            try:
                translation = LangTranslation.objects.get(id=trans_id, content__id=content_id)
                if translation.state != "sent" and translation.state != "received" and translation.state != "pending":
                    return Response({'detail':
                                         f'The translation {trans_id} state is {translation.state}, you can not modify it'
                                     }, status=status.HTTP_403_FORBIDDEN)
                if new_state:
                    translation.state = new_state
                if new_state_message:
                    translation.state_message = new_state_message
                if new_data:
                    translation.data = new_data

                translations_to_update.append(translation)
                updated.append(translation.id)

            except LangTranslation.DoesNotExist:
                errors.append({"detail": f"Translation with id {trans_id} not found"})

    if translations_to_update:
        try:
            content = Content.objects.get(id=content_id)
            content.generated_at = datetime.now()
            content.save()
        except Content.DoesNotExist:
            errors.append({"detail": f"Content with id {content_id} not found"})
        LangTranslation.objects.bulk_update(translations_to_update, ['state', 'state_message', 'data'])

    return Response({
        "updated_ids": updated,
        "errors": errors
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsCopywriter])
def delete_content_file(request, pk):
    content_file = get_object_or_404(ContentFile.objects.select_related('content__creator'), pk=pk)
    if content_file.content.creator != request.user:
        return Response(error_message("You do not have permission to delete this file"),
                        status=status.HTTP_403_FORBIDDEN)
    content_file.delete()
    return Response({"detail": "File deleted."}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsCopywriter])
def delete_s3file(request, user_id, content_id, file):
    content = get_object_or_404(Content.objects.only('s3files'), id=content_id)
    original_length = len(content.s3files)
    # Filter out the item with the matching key
    file_key = f"{user_id}/{content_id}/{file}"
    content.s3files = [file for file in content.s3files if file.get("key") != file_key]
    if len(content.s3files) == original_length:
        return Response({"detail": f"File with key '{file_key}' not found"}, status=status.HTTP_404_NOT_FOUND)
    content.save()
    return Response({"detail": f"File with key '{file_key}' deleted"}, status=status.HTTP_200_OK)


def get_input_schema(class_name):
    import importlib
    if not class_name:
        return None

    module_name = f"models.{class_name.lower()}.classes"
    class_name = class_name.title()
    class_name = class_name.replace("_", "")

    try:
        module = importlib.import_module(module_name)
        klass = getattr(module, class_name)
        return json.dumps(klass.model_json_schema())
    except (ModuleNotFoundError, AttributeError) as e:
        print(e, flush=True)
        return None


def get_output_schema(content):
    import importlib

    className = content.content_type.name
    category = content.data.get('type')

    if not className:
        return None

    module_name = f"models.{className.lower()}.classes"
    class_name = className.title()
    class_name = class_name.replace("_", "")

    try:
        module = importlib.import_module(module_name)
        klass = getattr(module, f"Merged{category.upper()}")
        return json.dumps(klass.model_json_schema())

    except (ModuleNotFoundError, AttributeError) as e:
        try:
            module = importlib.import_module(module_name)
            klass = getattr(module, f"{class_name}Out")
            return json.dumps(klass.model_json_schema())

        except (ModuleNotFoundError, AttributeError) as e:
            print(e, flush=True)
            return None


def get_output_schema_from_data(data):
    import importlib

    className = data['content_type'].name
    category = data['data'].get('type')

    if not className:
        return None

    module_name = f"models.{className.lower()}.classes"
    class_name = className.title()
    class_name = class_name.replace("_", "")

    try:
        module = importlib.import_module(module_name)
        klass = getattr(module, f"Merged{category.upper()}")
        return json.dumps(klass.model_json_schema())

    except (ModuleNotFoundError, AttributeError) as e:
        try:
            module = importlib.import_module(module_name)
            klass = getattr(module, f"{class_name}Out")
            return json.dumps(klass.model_json_schema())

        except (ModuleNotFoundError, AttributeError) as e:
            print(e, flush=True)
            return None


@api_view(['GET'])
@permission_classes([IsAuth])
def get_content_types(request):
    content_types = ContentType.objects.all()
    serializer = ContentTypeSerializer(content_types, many=True)
    param = request.GET.get("content_type")
    schema = get_input_schema(param)
    # print(json.dumps(schema, indent=2))
    response = {
        "content_types": serializer.data,
        "content_statuses": [key for key, _ in CONTENT_STATUSES],
        "content_states": [key for key, _ in CONTENT_STATES]
    }
    if schema:
        response['schema'] = schema
    return Response(response)


@api_view(['GET'])
@permission_classes([IsCopywriter])
def get_languages(request):
    languages = Language.objects.filter(active=True)
    serializer = LanguageSerializer(languages, many=True)
    return Response(serializer.data)


class LanguageActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['active']


class LanguageActive(APIView):
    '''
    curl -X GET http://localhost:8000/api/language_active/ \
     -H "Content-Type: application/json" \

    curl -X PATCH http://localhost:8000/api/language_active/ \
     -H "Content-Type: application/json" \
     -d '{"id": 1, "active": false}'
    '''
    permission_classes = [IsAdmin]

    def get(self, request):
        languages = Language.objects.all()
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)

    def patch(self, request):
        pk = request.data.get('id')
        language = get_object_or_404(Language, pk=pk)
        serializer = LanguageActiveSerializer(language, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': f'{language.name} updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsCopywriterOrAdmin])
def get_llms(request):
    if request.user.role == "amministratore":
        models = Prefetch('models')
    elif request.user.role == "copywriter":
        models = Prefetch('models', queryset=LLMModel.objects.filter(active=True))
    services = LLMService.objects.prefetch_related(models).all()
    serializer = LLMServiceSerializer(services, many=True)
    return Response({"llms": serializer.data})


@api_view(['PUT'])
@permission_classes([IsCopywriterOrAdmin])
def set_llm_model_active(request):
    model = get_object_or_404(LLMModel, id=request.data.get('id'))
    new_active_status = request.data.get("active")
    if new_active_status:
        response = requests.post(
            settings.AI_CORE_URL + f'/llm_models/activate?provider={model.service.name}&name={model.name}', json={})
    else:
        response = requests.post(
            settings.AI_CORE_URL + f'/llm_models/deactivate?provider={model.service.name}&name={model.name}', json={})
    # print("Response status code:", response.status_code, flush=True)
    # print("Response body from ai-core:", response.text, flush=True)
    return Response({"update": response.text})


@api_view(['POST'])
@permission_classes([IsCopywriter])
def translate_content(request):
    '''
    curl -X POST http://localhost:8001/api/translate_content/ \
         -H "Content-Type: application/json" \
         -d '{
        "content_id": 416, 
        "language_ids": [67, 64]
    }'
    '''
    content_id = request.data.get("content_id")
    language_ids = request.data.get("language_ids")

    if not content_id or not isinstance(language_ids, list):
        return Response({'detail': 'Missing content_id or language_ids must be a list.'},
                        status=status.HTTP_400_BAD_REQUEST)

    content = get_object_or_404(Content, pk=content_id)
    added_translations = []
    skipped_languages = []
    trans_objects = []

    for lang_id in language_ids:
        language = Language.objects.filter(pk=lang_id).first()
        if not language:
            skipped_languages.append({'language_id': lang_id, 'reason': 'Language not found'})
            continue

        if LangTranslation.objects.filter(content=content, language=language).exists():
            skipped_languages.append({'language': language.name, 'reason': 'Already exists'})
            continue

        trans = LangTranslation.objects.create(content=content, language=language, state='sent')
        added_translations.append({'language': language.name, 'translation_id': trans.id})
        trans_objects.append(trans)

    if trans_objects:
        content.status = "review_traduzioni"
        content.save()
        # send 'notify' to ai-core translate endpoint
        resp_data = get_trans_task_data(trans_objects)
        response = requests.post(settings.AI_CORE_URL + '/translate/', json=resp_data[0])
        # print("Response status code:", response.status_code, flush=True)
        # print("Response body:", response.text, flush=True)

    return Response(
        {'detail': 'Translation creation complete.', 'added': added_translations, 'skipped': skipped_languages},
        status=status.HTTP_207_MULTI_STATUS if skipped_languages else status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsTraduttore])
def update_translation_data(request):
    '''
    curl -X PUT http://localhost:8000/api/update_translation_data/ \
    -H "Content-Type: application/json" \
    -d '
          {
            "id": 205,
            "data": {...}
          }
    '
    '''
    payload = request.data
    trans_id = payload.get('id')

    if not trans_id:
        return Response(error_message("Translation id not provided"), status=status.HTTP_404_NOT_FOUND)

    translation = get_object_or_404(LangTranslation, id=trans_id)
    new_data = payload.get('data')
    if new_data:
        translation.data = new_data
        translation.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsTraduttore])
def retry_translation(request):
    '''
    curl -X PUT http://localhost:8001/api/retry_translation/ \
    -H "Content-Type: application/json" \
    -d '
          {
            "trans_id": 205,
            "retry_custom_prompt"
          }
    '
    '''
    payload = request.data
    trans_id = payload.get('trans_id')
    retry_custom_prompt = payload.get('retry_custom_prompt', "")

    if not trans_id:
        return Response(error_message("Translation id not provided"), status=status.HTTP_404_NOT_FOUND)

    translation = get_object_or_404(LangTranslation, id=trans_id)
    translation.state = "sent"
    translation.state_message = ""
    translation.save()
    resp_data = get_trans_task_data([translation])

    if retry_custom_prompt:
        _ = requests.post(
            f"{settings.AI_CORE_URL}/retry_translate/",
            params={'retry_custom_prompt': retry_custom_prompt},
            json=resp_data[0]
        )
    else:
        _ = requests.post(settings.AI_CORE_URL + '/translate/', json=resp_data[0])

    return Response(status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsCopywriter])
def remove_translation(request, translation_id):
    '''
    curl -X DELETE http://localhost:8001/api/remove_translation/265/ \
         -H "Content-Type: application/json"
    '''
    translation = get_object_or_404(LangTranslation, id=translation_id)
    translation.delete()
    return Response({'detail': 'Translation deleted successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsApprovatore])
def get_contents_to_review(request):
    contents = get_content_queryset().filter(status='review').order_by('-created_at')
    contents = get_contents_filtered(request, contents)
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


class ApproveContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['status', 'rejection_message']

    def validate(self, data):
        if self.instance and self.instance.status != 'review' or self.instance.status != "validata":
            raise serializers.ValidationError(
                f"Error content status '{self.instance.status}'"
            )
        return data


@api_view(['PUT'])
@permission_classes([IsApprovatore])
def publish_content(request, pk):
    content = get_object_or_404(Content, pk=pk)

    # clean all history of for the published content
    history_qs = Content.history.filter(id=content.id)
    if history_qs.exists():
        history_keys = [f['key'] for c in history_qs for f in c.s3files]
        content_keys = [f['key'] for f in content.s3files]
        # Find history keys that are not in content using set difference
        files_to_clear = list(set(history_keys) - set(content_keys))
        for f in files_to_clear:
            delete_s3_file(f)

    history_qs.delete()

    content.status = "pubblicata"
    content.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsApprovatore])
def approve_content(request, pk):
    content = get_object_or_404(Content, pk=pk)
    content.status = "bozza_validata"
    content.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsApprovatore])
def reject_content(request, pk):
    content = get_object_or_404(Content, pk=pk)
    content.translations.all().delete()
    content.status = "bozza_rifiutata"
    content.rejection_message = request.data.get("rejection_message", "")
    content.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsTraduttore])
def get_translations_to_review(request):
    user_langs = request.user.langs.all()
    contents = Content.objects.select_related('creator', 'content_type', 'language', 'llmmodel').prefetch_related(
        Prefetch('translations', queryset=LangTranslation.objects.filter(status='pending', language__in=user_langs))
    ).filter(
        status='review_traduzioni',
        translations__status='pending',
        translations__language__in=user_langs
    ).distinct().order_by('-created_at')
    contents = get_contents_filtered(request, contents)
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsTraduttore])
def get_translations_validated(request):
    user_langs = request.user.langs.all()
    contents = Content.objects.select_related('creator', 'content_type', 'language', 'llmmodel').prefetch_related(
        Prefetch('translations', queryset=LangTranslation.objects.filter(status='validata', language__in=user_langs))
    ).filter(
        status='review_traduzioni',
        translations__status='validata',
        translations__language__in=user_langs
    ).distinct().order_by('-created_at')
    contents = get_contents_filtered(request, contents)
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


class ApproveTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LangTranslation
        fields = ['status']

    def validate(self, data):
        if self.instance and self.instance.status == 'validata':
            raise serializers.ValidationError(
                f"Status already in '{self.instance.status}'"
            )
        return data


@api_view(['PATCH'])
@permission_classes([IsTraduttore])
def approve_translation(request, translation_pk):
    translation = get_object_or_404(LangTranslation, pk=translation_pk)
    serializer = ApproveTranslationSerializer(translation, data={'status': 'validata'}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsApprovatore])
def reject_translation(request, translation_pk):
    translation = get_object_or_404(LangTranslation, pk=translation_pk)
    rejection_message = request.data.get('rejection_message', '')
    translation.rejection_message = rejection_message
    translation.status = "rifiutata"
    translation.save()
    translation.content.status = "review_traduzioni"
    translation.content.save()
    return Response({"detail": "ok"}, status=200)


@api_view(['GET'])
@permission_classes([IsCopywriterOrApprovatore])
def get_contents_validated(request):
    contents = get_content_queryset().filter(status='validata')
    contents = get_contents_filtered(request, contents)
    contents = contents.order_by('-created_at')
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuth])
def get_contents_published(request):
    contents = get_content_queryset().filter(
        status='pubblicata',
    )
    contents = get_contents_filtered(request, contents)
    contents = contents.order_by('-created_at')
    paginator = PageNumberPagination()
    result_page = paginator.paginate_queryset(contents, request)
    serializer = ContentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


def get_contents_filtered(request, contents):
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    content_type = request.query_params.get('content_type')
    name = request.query_params.get('name')
    state = request.query_params.get('state')
    status = request.query_params.get('status')
    data_type = request.query_params.get('data_type')

    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            contents = contents.filter(created_at__date__gte=start_date)
    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            contents = contents.filter(created_at__date__lte=end_date)
    if content_type:
        contents = contents.filter(content_type__name=content_type)
    if name:
        contents = contents.filter(title__icontains=name)
    if state:
        contents = contents.filter(state=state)
    if status:
        contents = contents.filter(status=status)
    if data_type:
        contents = contents.filter(data__type__icontains=data_type)

    return contents


@api_view(['POST'])
@permission_classes([IsPublisher])
def gsheet_export(request):
    content_id = request.data.get('content_id')

    try:
        content = get_content_queryset().filter(pk=content_id).first()
        if not content:
            return Response({'error': 'Content not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    if content.status != "pubblicata":
        return Response({'error': 'Content must be published'}, status=status.HTTP_403_FORBIDDEN)

    gs = GSheetBuilder()

    try:
        return Response(gs.export_content(content), status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Failed to export to Google Sheets: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AuthTask])
def get_s3_file(request, user_id, content_id, file, file_name):
    '''
    curl -X GET http://localhost:8000/api/get_s3_file/4/290/1750888286.6994767_test_a.txt/test_a.txt/ -H "TaskToken:abc"
    '''
    file_format = request.GET.get("file_format")
    if file_format == "base64":
        file_key = f"{user_id}/{content_id}/{file}"
        base64_data = get_s3_file_base64(file_key)
        if base64_data is None:
            return Response({'detail': 'File not found in S3'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'file_key': file_key, 'base64': base64_data}, status=status.HTTP_200_OK)

    return stream_s3_file(request, user_id, content_id, file, file_name)


@api_view(['GET'])
@permission_classes([IsAuth])
def download_s3_file(request, user_id, content_id, file, file_name):
    return stream_s3_file(request, user_id, content_id, file, file_name)


def upload_to_s3(content_id, request):
    import time
    files = request.FILES.getlist('files')
    uploaded_files = []
    if settings.AWS_S3_BUCKET_NAME and files:
        if len(files) > 5:
            return None
        for file in files:
            seconds = time.time()
            file_key = f"{request.user.id}/{content_id}/{seconds}_{file.name}"
            fileUploaded = file_upload_to_s3(file, file_key)
            if fileUploaded == False:
                return None
            uploaded_files.append({"key": file_key, "name": file.name})
    return uploaded_files


@api_view(['POST'])
@permission_classes([IsAdmin])
def add_new_language(request):
    if request:
        name = request.data.get('name')
        if name and name != '':
            if Language.objects.filter(name=name).first():
                return Response({"Error": f"Language {name} already exists."}, status=status.HTTP_403_FORBIDDEN)
            else:
                Language.objects.create(name=name)
                return Response(status=status.HTTP_201_CREATED)
        else:
            return Response({"Error": "add a valid language name"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_403_FORBIDDEN)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name", "role", "roles", "langs"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['roles'] = [role.get_name_display().lower() for role in instance.roles.all()]
        return rep


@api_view(['GET'])
@permission_classes([IsAdmin])
def get_users(request, role=None):
    User = get_user_model()

    # Annotazione: guest_first = 0 se ha 'guest' come role o nei roles m2m, altrimenti 1
    users = User.objects.annotate(
        guest_first=Case(
            When(Q(role="guest") | Q(roles__name="guest"), then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    )

    # Filtro per ruolo, cercando sia in `role` che in `roles`
    if role:
        users = users.filter(Q(role=role) | Q(roles__name=role))
    else:
        users = users.exclude(pk=request.user.pk)

    # Evitiamo duplicati dovuti al join con roles
    users = users.distinct().order_by("guest_first", "role")

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdmin])
def set_user_role(request):
    pk = request.data.get("user_pk")
    new_role = request.data.get("new_role")
    User = get_user_model()
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(error_message("User not found"), status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data={"role": new_role}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdmin])
def get_user_langs(request, user_pk):
    user = get_object_or_404(get_user_model(), pk=user_pk)
    langs = user.langs.all()
    serializer = LanguageSerializer(langs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAdmin])
def set_user_langs(request, user_pk):
    user = get_object_or_404(get_user_model(), pk=user_pk)
    langs = request.data.get("langs", [])
    if not isinstance(langs, list):
        return Response({"detail": "Expected a list of language IDs."}, status=status.HTTP_400_BAD_REQUEST)
    # Replace the user's langs with new ones
    user.langs.set(langs)
    user.save()
    langs = user.langs.all()
    serializer = LanguageSerializer(langs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class AddNewLLM(APIView):
    '''
    curl -X POST http://localhost:8000/api/add_new_llm/ \
    -H "Content-Type: application/json" \
    -d '
    {
        "llm_string": "openai:gpt-4",
        "active": true,
    }
    '''
    permission_classes = [IsAdmin]

    def post(self, request):
        llm_string = request.data.get("llm_string")
        if not llm_string or ":" not in llm_string:
            return Response({"error": "Invalid format. Use provider:model e.g: openai:gpt-4"},
                            status=status.HTTP_400_BAD_REQUEST)

        service_name, model_name = llm_string.split(":", 1)
        api_key = request.data.get("api_key", "")
        active = request.data.get("active", False)
        # state_message = request.data.get("state_message", "")

        # Get or create service
        service, created = LLMService.objects.get_or_create(name=service_name)

        # Check if model already exists
        if LLMModel.objects.filter(service=service, name=model_name).exists():
            return Response({"error": f"Model '{model_name}' already exists for service '{service_name}'"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create new model
        model = LLMModel.objects.create(
            service=service,
            name=model_name,
            model_id=model_name,
            api_key=api_key,
            active=active,
        )

        return Response({
            "message": "LLM model added",
            "service": service.name,
            "model": model.name
        }, status=status.HTTP_201_CREATED)


class LLMServiceCreate(APIView):
    '''
    curl -X POST http://localhost:8000/api/llm_service_create/ \
        -H "Content-Type: application/json" \
        -d '{
        "name": "my new llm service",
        "multimodal": true
    }'
    '''
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = LLMServiceSerializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            return Response(LLMServiceSerializer(service).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LLMModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        exclude = ['api_key']


class LLMModelCreate(APIView):
    '''
    curl -X POST http://localhost:8000/api/llm_model_create/ \
        -H "Content-Type: application/json" \
        -d '{
        "service": 1,
        "name": "test1",
        "model_id": "test1",
        "active": true
    }'
    '''
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = LLMModelCreateSerializer(data=request.data)
        if serializer.is_valid():
            model = serializer.save()
            return Response(LLMModelCreateSerializer(model).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AuthTask])
def LLMS(request):
    '''
    how to filter:
    api/llms/?multimodal=true
    api/llms/?multimodal=false
    '''
    multimodal = request.query_params.get('multimodal')
    queryset = LLMService.objects.prefetch_related('models')

    if multimodal is not None:
        multimodal_bool = multimodal.lower() == 'true'
        queryset = queryset.filter(multimodal=multimodal_bool)

    result = []
    for service in queryset.all():
        for model in service.models.all():
            result.append(f"{service.name.lower()}:{model.name.lower()}")
    return Response(result)


class LLMProviders(APIView):
    '''
    how to filter:
    api/llm_providers/?multimodal=true
    api/llm_providers/?multimodal=false
    '''
    permission_classes = [AuthTask]

    def get(self, request):
        multimodal = request.query_params.get('multimodal')

        queryset = LLMService.objects.all()
        if multimodal is not None:
            multimodal_bool = multimodal.lower() == 'true'
            queryset = queryset.filter(multimodal=multimodal_bool)

        serializer = LLMServiceSerializer(queryset, many=True)
        return Response(serializer.data)


class LLMModels(APIView):
    '''
    curl -X PUT https://test.lvr.inventiohub.com/api/llm_models/ \
      -H "Content-Type: application/json" \
      -H "TaskToken: abc" \
      -d '{
        "service": 1,
        "name": "GPT-4 Turbo",
        "model_id": "gpt-4-turbo",
        "api_key": "sk-updated-api-key",
        "active": false,
        "state_message": "test message"
      }'
    '''
    permission_classes = [AuthTask]

    def get(self, request):
        service = request.query_params.get('service')
        active = request.query_params.get('active')

        queryset = LLMModel.objects.all()
        if service:
            queryset = queryset.filter(service__name=service)
        if active == 'true':
            queryset = queryset.filter(active=True)

        serializer = LLMModelSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LLMModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        service_name = request.data.get('provider_name')
        model_name = request.data.get('model_name')

        if not service_name or not model_name:
            return Response(
                {"detail": "Both 'service_name' and 'model_name' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            instance = LLMModel.objects.select_related('service').get(
                service__name__iexact=service_name,
                name__iexact=model_name
            )
        except LLMModel.DoesNotExist:
            return Response(
                {"detail": f"No model found for service '{service_name}' and model '{model_name}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LLMModelSerializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


@api_view(['GET'])
@permission_classes([IsAuth])
def get_notifications(request):
    notifications = Notification.objects.filter(receiver_id=request.user.pk).order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuth])
def consume_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, receiver_id=request.user.pk)
    message = notification.message
    notification.delete()
    return Response({"detail": f"Notification with message '{message}' consumed"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_create_task(request):
    '''
    available params: 
    n=5 (100 at once max)
    content_type=HOMEPAGE
    llm_name=gpt-4o
    '''
    if not settings.DEBUG:
        return Response({"detail": "you can't run this in prod"}, status=status.HTTP_403_FORBIDDEN)

    import os
    n = int(request.query_params.get("n", 1))  # Default to 1 if not provided
    if n > 100:
        n = 100
    content_type_name = request.GET.get("content_type", "HOMEPAGE")
    llm_name = request.GET.get("llm_name", "gpt-4o")

    User = get_user_model()
    user = User.objects.get(username='copywriter')

    content_type = get_object_or_404(ContentType, name=content_type_name)
    language = get_object_or_404(Language, lang_alpha2="en", country_alpha2="US")
    llmmodel = get_object_or_404(LLMModel, name=llm_name)

    contents = []

    base_dir = os.path.join(settings.BASE_DIR, f"tests/inputs/{content_type.name.lower()}/")
    primary_path = os.path.join(base_dir, "1.json")
    fallback_path = os.path.join(base_dir, "input_1.json")

    if os.path.exists(primary_path):
        target_path = primary_path
    elif os.path.exists(fallback_path):
        target_path = fallback_path
    else:
        return Response({"Error": f"Neither '1.json' nor 'input_1.json' found in {base_dir}"}, status=500)

    f = open(target_path, 'r', encoding='utf-8')
    json_data = json.load(f)
    input_data = json_data.get("data", {})

    for i in range(n):
        contents.append(Content(
            creator=user,
            content_type=content_type,
            language=language,
            llmmodel=llmmodel,
            title=f'Test_task_{i + 1}',
            custom_prompt='',
            state='sent',
            sent_at=datetime.now(),
            state_message='',
            status='bozza',
            data=input_data
        ))

    # Bulk insert
    created_contents = Content.objects.bulk_create(contents)

    for content in created_contents:
        content.schema = json.loads(get_output_schema(content))
        content.save()
        # send notify to ai core
        serializer = ContentSerializer(content)
        requests.post(settings.AI_CORE_URL + '/generate/', json=serializer.data)

    return Response({"created_ids": [c.id for c in created_contents], "count": len(created_contents)}, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_create_trans_task(request):
    '''
    available params: 
    n=5 (100 at once max)
    content_type=HOMEPAGE
    llm_name=gpt-4o
    '''
    if not settings.DEBUG:
        return Response({"detail": "you can't run this in prod"}, status=status.HTTP_403_FORBIDDEN)

    import os
    import random
    n = int(request.query_params.get("n", 1))  # Default to 1 if not provided
    if n > 100:
        n = 100
    content_type_name = request.GET.get("content_type", "HOMEPAGE")
    llm_name = request.GET.get("llm_name", "gpt-4o")

    User = get_user_model()
    user = User.objects.get(username='copywriter')

    content_type = get_object_or_404(ContentType, name=content_type_name)
    language = get_object_or_404(Language, lang_alpha2="en", country_alpha2="US")
    llmmodel = get_object_or_404(LLMModel, name=llm_name)

    contents = []

    base_dir = os.path.join(settings.BASE_DIR, f"tests/outputs/generation/{content_type.name.lower()}/")
    primary_path = os.path.join(base_dir, "1.json")
    fallback_path = os.path.join(base_dir, "output_1.json")
    if os.path.exists(primary_path):
        target_path = primary_path
    elif os.path.exists(fallback_path):
        target_path = fallback_path
    else:
        return Response({"Error": f"Neither '1.json' nor 'input_1.json' found in {base_dir}"}, status=500)

    f = open(target_path, 'r', encoding='utf-8')
    json_data = json.load(f)
    input_data = json_data.get("data", {})

    for i in range(n):
        contents.append(Content(
            creator=user,
            content_type=content_type,
            language=language,
            llmmodel=llmmodel,
            title=f'Test_task_{i + 1}',
            custom_prompt='',
            state='success',
            sent_at=datetime.now(),
            state_message='',
            status='review_traduzioni',
            data=input_data
        ))

    created_contents = Content.objects.bulk_create(contents)

    for content in created_contents:
        content.schema = json.loads(get_output_schema(content))
        content.save()

    translations = [
        LangTranslation(
            content=content,
            language=random.choice(list(Language.objects.all())),
            state='sent',
            status='pending'
        )
        for content in created_contents
    ]
    created_translations = LangTranslation.objects.bulk_create(translations)
    resp_data = get_trans_task_data(created_translations)
    response = requests.post(settings.AI_CORE_URL + '/translate/', json=resp_data[0])

    return Response({"created_ids": [c.id for c in created_contents], "count": len(created_contents)}, status=201)
