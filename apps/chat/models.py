"""
Chat models: Session, Message, Diagnosis, Treatment, Embedding.
All use UUID primary keys. Compatible with SQLite and PostgreSQL.
"""
import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator


class Session(models.Model):
    """A chat consultation session — scoped to a user."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("diagnosed", "Diagnosed"),
        ("closed", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        db_index=True,
    )
    tenant_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    pet_breed = models.CharField(max_length=100, blank=True, null=True)
    pet_name = models.CharField(max_length=100, blank=True, null=True)
    pet_age = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20, default="active", choices=STATUS_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        indexes = [
            models.Index(fields=["user", "updated_at"]),
            models.Index(fields=["tenant_id"]),
        ]
        ordering = ["-updated_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pet_age:
            try:
                age_val = int(self.pet_age)
                if age_val < 0 or age_val > 50:
                    raise ValidationError({"pet_age": "Pet age must be between 0 and 50."})
            except ValueError:
                pass  # Allow string ages like "3 months"

    def __str__(self):
        return f"Session {self.id.hex[:8]} ({self.status})"


class Message(models.Model):
    """A single message in a chat session (user or assistant)."""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(
        validators=[MinLengthValidator(1), MaxLengthValidator(4000)]
    )
    image_url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]
        ordering = ["created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError({"role": f"Role must be 'user' or 'assistant'."})

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"


class Diagnosis(models.Model):
    """AI-generated diagnosis linked to a session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="diagnoses",
        db_index=True,
    )
    disease = models.CharField(max_length=100)
    confidence = models.FloatField(null=True, blank=True)
    symptoms_summary = models.TextField(null=True, blank=True)
    treatment_plan = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_diagnoses"
        verbose_name_plural = "diagnoses"
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["disease"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Diagnosis: {self.disease} ({self.id.hex[:8]})"


class Treatment(models.Model):
    """Reference treatment data for veterinary conditions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disease = models.CharField(max_length=100, db_index=True)
    pet_type = models.CharField(max_length=50, blank=True, null=True)
    severity = models.CharField(max_length=20, blank=True, null=True)
    home_care = models.TextField(blank=True, null=True)
    medication = models.TextField(blank=True, null=True)
    when_to_see_vet = models.TextField(blank=True, null=True)
    prevention = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "chat_treatments"
        ordering = ["disease", "severity"]
        constraints = [
            models.UniqueConstraint(
                fields=["disease", "pet_type", "severity"],
                name="unique_chat_treatment_per_type_severity",
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.disease or not self.disease.strip():
            raise ValidationError({"disease": "Disease name is required."})

    def __str__(self):
        return f"{self.disease} ({self.severity or 'general'})"


class Embedding(models.Model):
    """
    Vector embeddings for RAG (Retrieval-Augmented Generation).
    Stores vectors as JSON arrays — compatible with SQLite.
    For PostgreSQL pgvector performance, use the original project's setup.
    """

    SOURCE_TYPES = [
        ("symptom_case", "Symptom Case"),
        ("treatment", "Treatment"),
    ]

    id = models.AutoField(primary_key=True)
    content = models.TextField()
    embedding = models.JSONField(
        help_text="Vector embedding stored as JSON array (384 floats)."
    )
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES, db_index=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_embeddings"
        indexes = [
            models.Index(fields=["source_type"]),
        ]

    def __str__(self):
        return f"Embedding #{self.id} ({self.source_type})"
