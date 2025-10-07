from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Role, CustomUser, Content, ContentFile, ContentType, Language, LangTranslation, LLMService, LLMModel, Notification
from simple_history.admin import SimpleHistoryAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Aggiungi il campo role ecc.. alla visualizzazione dei dettagli
    fieldsets = UserAdmin.fieldsets + (
        ("Ruolo", {"fields": ("role", "langs", 'roles')}),
    )
    # Aggiungi il campo role ecc... anche alla form di creazione dell'utente (opzionale)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Ruolo", {"fields": ("role","langs", "roles")}),
    )
    # campi da visualizzare nella lista utenti 
    list_display = ["username", 'first_name', 'last_name', "email", "role", "is_staff"]

admin.site.register(CustomUser, CustomUserAdmin)
#admin.site.register(CustomUser)

admin.site.register(ContentType)
admin.site.register(Language)
admin.site.register(ContentFile)
admin.site.register(LangTranslation)
admin.site.register(LLMService)
admin.site.register(LLMModel)
admin.site.register(Role)
admin.site.register(Notification)

class ContentHistoryAdmin(SimpleHistoryAdmin):
    list_display = ['__str__']
    history_list_display = ["title"]

#admin.site.register(Content)
admin.site.register(Content, ContentHistoryAdmin)
#admin.site.register(Content, SimpleHistoryAdmin)
