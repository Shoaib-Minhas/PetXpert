from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class AppointmentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    NO_SHOW = 'NO_SHOW', 'No Show'

class Appointment(BaseModel):
    pet_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='appointments_as_owner', db_index=True)
    veterinarian = models.ForeignKey('accounts.VeterinarianProfile', on_delete=models.RESTRICT, related_name='appointments_as_vet', db_index=True)
    pet = models.ForeignKey('pets.Pet', on_delete=models.RESTRICT, related_name='appointments')
    # slot = models.OneToOneField('veterinarians.AvailabilitySlot', on_delete=models.CASCADE, unique=True) # Will implement when vet app is ready
    scheduled_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING, db_index=True)
    fee_charged = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_appointments')

    class Meta:
        db_table = 'appointments_appointment'
        constraints = [
            models.CheckConstraint(condition=models.Q(scheduled_at__gt=models.functions.Now()), name='chk_scheduled_future'),
            models.CheckConstraint(condition=models.Q(fee_charged__gte=0), name='chk_fee_non_negative'),
            models.CheckConstraint(condition=models.Q(duration_minutes=60), name='chk_duration_valid'),
        ]
