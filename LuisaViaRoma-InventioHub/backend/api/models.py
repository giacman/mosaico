from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.db.models import JSONField, QuerySet, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from enum import Enum

class RoleName(str, Enum):
    Copywriter = "copywriter"
    Approver = "approvatore"
    Translator = "traduttore"
    Publisher = "publisher"

ROLE_CHOICES = (
    ('guest', 'guest'),
    ('amministratore', 'Amministratore'),
    ('copywriter', 'Copywriter'),
    ('approvatore', 'Approvatore'),
    ('traduttore', 'Traduttore'),
    ('publisher', 'Publisher'),
)

class Role(models.Model):
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    def __str__(self):
        return self.get_name_display()

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    langs = models.ManyToManyField("Language", blank=True)
    # user may change role based on roles assigned
    roles = models.ManyToManyField(Role, blank=True)

    def __str__(self):
        return self.username

CONTENT_TYPES = [
    ('editorial', 'EDITORIAL'),
    ('homepage', 'HOMEPAGE'),
    ('omni_message', 'OMNI_MESSAGE'),
    ('omni_banner', 'OMNI_BANNER'),
    ('social_organic', 'SOCIAL_ORGANIC'),
    ('social_paid', 'SOCIAL_PAID'),
    ('marketing_campaign', 'MARKETING_CAMPAIGN'),
    ('newsletter', 'NEWSLETTER'),
]

LANGS = [
    ('English', 'en', 'US'),
    ('English', 'en', 'GB'),
    ('French', 'fr', 'FR'),
    ('French', 'fr', 'CA'),
    ('Spanish', 'es', 'ES'),
    ('Spanish', 'es', 'MX'),
    ('German', 'de', 'DE'),
    ('Italian', 'it', 'IT'),
    ('Portuguese', 'pt', 'PT'),
    ('Portuguese', 'pt', 'BR'),
    ('Arabic', 'ar', 'SA'),
    ('Arabic', 'ar', 'EG'),
    ('Chinese (Simplified)', 'zh', 'CN'),
    ('Chinese (Traditional)', 'zh', 'TW'),
    ('Russian', 'ru', 'RU'),
    ('Japanese', 'ja', 'JP'),
    ('Korean', 'ko', 'KR'),
    ('Dutch', 'nl', 'NL'),
    ('Hindi', 'hi', 'IN'),
    ('Swedish', 'sv', 'SE'),
    ('Polish', 'pl', 'PL'),
    ('Turkish', 'tr', 'TR'),
    ('Hebrew', 'he', 'IL'),
    ('Norwegian', 'no', 'NO'),
    ('Finnish', 'fi', 'FI'),
    ('Greek', 'el', 'GR'),
    ('Czech', 'cs', 'CZ'),
    ('Hungarian', 'hu', 'HU'),
    ('Danish', 'da', 'DK'),
    ('Thai', 'th', 'TH'),
    ('Vietnamese', 'vi', 'VN'),
]

TRANS_STATUSES = [
    ('pending', 'Pending'),
    ('validata', 'Validata'),
    ('rifiutata', 'Rifiutata'),
]

CONTENT_STATES = [
    ('local', 'local'),
    ('sent', 'sent'),
    ('received', 'received'),
    ('pending', 'pending'),
    ('failed', 'failed'),
    ('success', 'success'),
]

CONTENT_STATUSES = [
    ('bozza', 'Bozza'),
    ('review', 'Review'),
    ('bozza_rifiutata', 'Bozza Rifiutata'),
    ('bozza_validata', 'Bozza Validata'),
    ('review_traduzioni', 'Review Traduzioni'),
    ('validata', 'Validata'),
    ('pubblicata', 'Pubblicata'),
]

class ContentType(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name 

class Language(models.Model):
    name = models.CharField(max_length=20) # english
    lang_alpha2 = models.CharField(max_length=2) # en
    country_alpha2 = models.CharField(max_length=2) # us
    active = models.BooleanField(default=True)
    def __str__(self):
        return f'{self.name} - {self.lang_alpha2}_{self.country_alpha2}'

class LLMService(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(blank=True, null=True)
    multimodal = models.BooleanField(default=False) 
    def __str__(self):
        return self.name

class LLMModel(models.Model):
    service = models.ForeignKey(LLMService, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    model_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100)
    active = models.BooleanField(default=False) 
    state_message = models.CharField(blank=True)
    def __str__(self):
        return f"{self.service.name} - {self.name}"

import warnings
class NaiveDateTimeField(models.DateTimeField):
    """
    A DateTimeField that accepts naive datetimes without warnings.
    """
    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if value is not None and timezone.is_naive(value):
            # Suppress the warning for this specific field
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                return value
        return value
    
    def to_python(self, value):
        # Suppress warnings during value conversion
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return super().to_python(value)

class Content(models.Model): 
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_content')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="language") 
    llmmodel = models.ForeignKey(LLMModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    custom_prompt = models.TextField(blank=True)
    schema = JSONField(default=dict, blank=True, null=True)
    data = JSONField(default=dict, blank=True, null=True)
    state = models.CharField(max_length=20, choices=CONTENT_STATES, default='local')
    state_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CONTENT_STATUSES, default='bozza')
    rejection_message = models.TextField(blank=True)
    s3files = JSONField(default=list, blank=True, null=True)
    history = HistoricalRecords(excluded_fields=['state', 'schema', 'state_message', 'sent_at', 'generated_at', 'rejection_message'])
    def __str__(self):
        return f'{self.title} \
        | {self.content_type.name} \
        | {self.created_at.strftime("%d-%m-%Y %H:%M")} \
        | {self.creator.username}'

    _updated_by_user = None
    def set_updated_by(self, user):
        self._updated_by_user = user

    def save(self, *args, **kwargs):
        if self._updated_by_user:
            pass

        if self.pk:
            old = Content.objects.get(pk=self.pk)
            if old.status != self.status:
                if self.status == "review":
                    approvers = get_user_model().objects.filter(
                        Q(role=RoleName.Approver) | Q(roles__name=RoleName.Approver)
                    ).distinct()
                    add_notifications(approvers, RoleName.Approver, 
                        f"{self.title} is in review", 
                        "/",
                        self.pk
                    )

                if self.status == "bozza_validata":
                    status = "accepted"
                    add_notifications(self.creator, RoleName.Copywriter, 
                        f"{self.title} has been {status}",
                        "translations",
                        self.pk
                    )

                if self.status == "bozza_rifiutata":
                    status = "rejected"
                    add_notifications(self.creator, RoleName.Copywriter,
                        f"{self.title} has been {status}",
                        "copywriter",
                        self.pk
                    )

                if self.status == "validata":
                    approvers = get_user_model().objects.filter(
                        Q(role=RoleName.Approver) | Q(roles__name=RoleName.Approver)
                    ).distinct() 
                    add_notifications(approvers, RoleName.Approver, 
                        f"{self.title} is in final review",
                        "/validated", 
                        self.pk
                    )

                if self.status == "pubblicata":
                    publishers = get_user_model().objects.filter(
                        Q(role=RoleName.Publisher) | Q(roles__name=RoleName.Publisher)
                    ).distinct() 
                    add_notifications(publishers, RoleName.Publisher, 
                        f"{self.title} has been published",
                        "/", 
                        self.pk
                    )

        super().save(*args, **kwargs)

class ContentFile(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=1024)
    def __str__(self):
        return f'{self.name} - {self.key}'

class LangTranslation(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    data = JSONField(default=dict, blank=True, null=True)
    state = models.CharField(max_length=20, choices=CONTENT_STATES, default='local')
    state_message = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=TRANS_STATUSES, default='pending')
    rejection_message = models.TextField(blank=True)
    class Meta:
        #unique_together = ('content', 'language')
        constraints = [
            models.UniqueConstraint(fields=['content', 'language'], name='unique_content_language')
    ]
    def __str__(self):
        return f'{self.content.title} - {self.language.name}'

    def save(self, *args, **kwargs):
        if self.pk is None:
            translators = get_user_model().objects.filter(
                Q(role=RoleName.Translator) | Q(roles__name=RoleName.Translator)
            ).all() 
            add_notifications(translators, RoleName.Translator, 
                f"[{self.content.title}]{self.language.name} is in {'translation' if self.status == 'pending' else  self.status  }",
                "/", 
                self.content.id 
            )
        else:
            old = LangTranslation.objects.filter(pk=self.pk).values("status").first()
            if old['status'] == "pending" and old['status'] != self.status:
                new_status = "validated" if self.status == "validata" else "rejected"
                add_notifications(self.content.creator, RoleName.Copywriter, 
                    f"{self.language.name} has been {new_status}",
                    "/translations",
                    self.content.id 
                )
        super().save(*args, **kwargs)

class Notification(models.Model):
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    role_name = models.CharField(max_length=20)
    link = models.CharField(max_length=50)
    modal_id = models.IntegerField()
    def __str__(self):
        return f'{self.receiver.first_name} {self.receiver.last_name} - {self.message}'

def add_notifications(receivers, role_name, message, link, modal_id):
    if not receivers:
        return  # Skip if empty or None
    if isinstance(receivers, QuerySet):
        notifications = [
            Notification(receiver=receiver, message=message, role_name=role_name, link=link, modal_id=modal_id)
            for receiver in receivers
        ]
        Notification.objects.bulk_create(notifications)
    else:
        # Single receiver case
        Notification.objects.create(receiver=receivers, message=message, role_name=role_name, link=link, modal_id=modal_id)
