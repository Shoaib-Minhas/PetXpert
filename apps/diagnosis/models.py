from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class DiagnosisInputType(models.TextChoices):
    IMAGE = 'IMAGE', 'Image'
    SYMPTOM = 'SYMPTOM', 'Symptom'
    BOTH = 'BOTH', 'Both'

class DiagnosisSeverity(models.TextChoices):
    LOW = 'LOW', 'Low'
    MODERATE = 'MODERATE', 'Moderate'
    HIGH = 'HIGH', 'High'
    EMERGENCY = 'EMERGENCY', 'Emergency'

class DiagnosisStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'

class DiagnosisRecord(BaseModel):
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='diagnoses', db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    input_type = models.CharField(max_length=20, choices=DiagnosisInputType.choices)
    symptom_text = models.TextField(blank=True, null=True)
    predicted_diseases = models.JSONField(default=list)  # Using JSONField for JSONB in Postgres
    severity = models.CharField(max_length=20, choices=DiagnosisSeverity.choices, db_index=True)
    risk_score = models.DecimalField(max_digits=4, decimal_places=3)
    status = models.CharField(max_length=20, choices=DiagnosisStatus.choices, default=DiagnosisStatus.PENDING, db_index=True)
    celery_task_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    model_version = models.CharField(max_length=20)
    inference_time_ms = models.IntegerField(null=True)

    class Meta:
        db_table = 'diagnosis_diagnosisrecord'
        constraints = [
            models.CheckConstraint(condition=models.Q(risk_score__range=(0.0, 1.0)), name='chk_risk_score_range'),
        ]
