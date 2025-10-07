"""
URL configuration for inventio_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api import views as api 
#from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/google/callback/", api.google_login, name="google_login"),
    #path('api/login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/', api.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('api/login/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/login/refresh/', api.CustomTokenRefreshView.as_view(), name='token_refresh'),

    path('api/sync_roles/', api.SyncRoles.as_view(), name='sync_roles'),
    path('api/get_role/', api.get_role, name='get_role'),
    path('api/change_role/', api.change_role, name='change_role'),

    path('api/create_content/', api.create_content, name='create_content'),
    path('api/get_content/<int:pk>/', api.get_content, name='get_content'),
    path('api/get_content_history/<int:pk>/', api.get_content_history, name='get_content_history'),
    path('api/restore_content/<int:content_id>/<int:history_id>/', api.restore_content, name='restore_content'),
    path('api/update_content/<int:pk>/', api.update_content, name='update_content'),
    path('api/send_to_content_review/<int:pk>/', api.send_to_content_review, name='send_to_content_review'),
    path('api/send_to_final_review/<int:pk>/', api.send_to_final_review, name='send_to_final_review'),
    path('api/send_to_ai/<int:pk>/', api.send_to_ai, name='send_to_ai'),
    path('api/send_in_review_translation/', api.send_in_review_translation, name='send_in_review_translation'),
    path('api/get_contents/', api.get_contents, name='get_contents'),
    path('api/get_contents/<str:filter>/', api.get_contents, name='get_contents'),

    path('api/delete_content_file/<int:pk>/', api.delete_content_file, name='delete_content_file'),
    path('api/delete_s3file/<int:user_id>/<int:content_id>/<str:file>/', api.delete_s3file, name='delete_s3file'),
    path('api/get_s3_file/<int:user_id>/<int:content_id>/<str:file>/<str:file_name>/', api.get_s3_file, name='get_s3_file'),
    path('api/download_s3_file/<int:user_id>/<int:content_id>/<str:file>/<str:file_name>/', api.download_s3_file, name='download_s3_file'),

    path('api/get_content_types/', api.get_content_types, name='get_content_types'),
    path('api/get_languages/', api.get_languages, name='get_languages'),
    path('api/get_llms/', api.get_llms, name='get_llms'),
    path('api/set_llm_model_active/', api.set_llm_model_active, name='set_llm_model_active'),

    path('api/translate_content/', api.translate_content, name='translate_content'),
    path('api/update_translation_data/', api.update_translation_data, name='update_translation_data'),
    path('api/retry_translation/', api.retry_translation, name='retry_translation'),
    path('api/remove_translation/<int:translation_id>/', api.remove_translation, name='remove_translation'),

    path('api/language_active/', api.LanguageActive.as_view(), name='language_active'),

    path('api/get_contents_validated/', api.get_contents_validated, name='get_contents_validated'),
    path('api/get_contents_published/', api.get_contents_published, name='get_contents_published'),

    path('api/gsheet_export/', api.gsheet_export, name='gsheet_export'),

    # approvatore
    path('api/get_contents_to_review/', api.get_contents_to_review, name='get_contents_to_review'),
    path('api/publish_content/<int:pk>/', api.publish_content, name='publish_content'),
    path('api/approve_content/<int:pk>/', api.approve_content, name='approve_content'),
    path('api/reject_content/<int:pk>/', api.reject_content, name='reject_content'),
    path('api/get_translations_to_review/', api.get_translations_to_review, name='get_translations_to_review'),
    path('api/get_translations_validated/', api.get_translations_validated, name='get_translations_validated'),
    path('api/approve_translation/<int:translation_pk>/', api.approve_translation, name='approve_translation'),
    path('api/reject_translation/<int:translation_pk>/', api.reject_translation, name='reject_translation'),

    # amministratore
    path('api/add_new_language/', api.add_new_language, name='add_new_language'),
    path('api/add_new_llm/', api.AddNewLLM.as_view(), name="add_new_llm"),
    path('api/get_users/', api.get_users, name='get_users'),
    path('api/get_users/<str:role>/', api.get_users, name='get_users'),
    path('api/set_user_role/', api.set_user_role, name='set_user_role'),
    path('api/get_user_langs/<int:user_pk>/', api.get_user_langs, name='get_user_langs'),
    path('api/set_user_langs/<int:user_pk>/', api.set_user_langs, name='set_user_langs'),

    # endpoint for ai-core
    path('api/get_generation_tasks/', api.get_generation_tasks, name='get_generation_tasks'),
    path('api/update_generation_task/', api.update_generation_task, name='update_generation_task'),
    path('api/get_trans_tasks/', api.get_trans_tasks, name='get_trans_tasks'),
    path('api/update_trans_tasks/', api.update_trans_tasks, name='update_trans_tasks'),

    # Add new LLM services (providers) and new LLM models
    #path('api/llm_service_create/', api.LLMServiceCreate.as_view(), name="llm_service_create"),
    #path('api/llm_model_create/', api.LLMModelCreate.as_view(), name="llm_service_create"),

    # LLM providers and models
    path('api/llms/', api.LLMS, name="llms"),
    path('api/llm_providers/', api.LLMProviders.as_view(), name="llm_providers"),
    path('api/llm_models/', api.LLMModels.as_view(), name="llm_models"),

    path('api/get_notifications/', api.get_notifications, name="get_notifications"),
    path('api/consume_notification/<int:notification_id>/', api.consume_notification, name="consume_notification"),

    path('api/test_create_task/', api.test_create_task, name='test_create_task'),
    path('api/test_create_trans_task/', api.test_create_trans_task, name='test_create_trans_task'),
]
