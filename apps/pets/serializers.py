from rest_framework import serializers
from .models import Pet, PetSpecies, PetGender


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'species', 'breed', 'date_of_birth', 'gender',
            'weight_kg', 'is_neutered', 'microchip_number', 'allergies', 'blood_type', 'picture'
        ]
        read_only_fields = ['id', 'owner']
    
    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        return value
    
    def validate_date_of_birth(self, value):
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
    
    def update(self, instance, validated_data):
        # Handle picture removal
        if 'picture' in validated_data and validated_data['picture'] == '':
            validated_data['picture'] = None
        return super().update(instance, validated_data)
