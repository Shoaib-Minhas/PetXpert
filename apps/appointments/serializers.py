from rest_framework import serializers
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id', 'veterinarian', 'pet', 'scheduled_at', 'duration_minutes',
            'status', 'fee_charged', 'reason', 'cancelled_by'
        ]
        read_only_fields = ['id', 'status', 'cancelled_by']
    
    def validate_scheduled_at(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment must be scheduled in the future.")
        return value
    
    def validate_duration_minutes(self, value):
        if value != 60:
            raise serializers.ValidationError("Duration must be 60 minutes.")
        return value
    
    def validate_fee_charged(self, value):
        if value < 0:
            raise serializers.ValidationError("Fee cannot be negative.")
        return value
