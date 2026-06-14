from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    REFUNDED = 'REFUNDED', 'Refunded'
    FAILED = 'FAILED', 'Failed'
    PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED', 'Partially Refunded'

class Payment(BaseModel):
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.RESTRICT, related_name='payment')
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='PKR')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True)
    gateway = models.CharField(max_length=50)
    gateway_txn_id = models.CharField(max_length=200, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments_payment'
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='chk_amount_positive'),
        ]
