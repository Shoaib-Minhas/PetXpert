from django.db import models
from apps.core.models import BaseModel

class Prescription(BaseModel):
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, related_name='prescriptions', db_index=True)
    issuing_vet = models.ForeignKey('accounts.VeterinarianProfile', on_delete=models.CASCADE, related_name='issued_prescriptions')
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='prescriptions', db_index=True)
    diagnosis_text = models.TextField()
    instructions = models.TextField()
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    pdf_s3_key = models.CharField(max_length=500, blank=True, null=True)
    is_finalized = models.BooleanField(default=False)

    class Meta:
        db_table = 'prescriptions_prescription'

class PrescriptionItem(BaseModel):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'prescriptions_prescriptionitem'
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0, duration_days__gt=0), name='chk_dosage_positive'),
        ]
