from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'appointment', 'payer', 'amount', 'currency', 'status',
            'gateway', 'gateway_txn_id', 'paid_at'
        ]
        read_only_fields = ['id', 'status', 'paid_at']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value
