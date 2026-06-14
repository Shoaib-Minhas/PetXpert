from rest_framework import serializers
from .models import User, VeterinarianProfile, VeterinarianReview

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar', 'role']
        read_only_fields = ['id', 'email', 'role']

class VeterinarianProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = VeterinarianProfile
        fields = [
            'id', 'user', 'profile_image', 'license_number', 'status', 'years_experience', 
            'consultation_fee', 'bio', 'avg_rating', 'rating_count', 'total_consultations', 'location',
            'specialization', 'clinic_name', 'clinic_address', 'phone_number', 'qualification'
        ]
        read_only_fields = ['id', 'user', 'status', 'avg_rating', 'rating_count', 'total_consultations']


class VeterinarianReviewSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    veterinarian_name = serializers.CharField(source='veterinarian.user.full_name', read_only=True)
    
    class Meta:
        model = VeterinarianReview
        fields = [
            'id', 'veterinarian', 'patient', 'patient_name', 'veterinarian_name', 
            'appointment', 'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate(self, data):
        """
        Validate that:
        1. The patient has a completed appointment with the veterinarian
        2. The patient is not reviewing themselves (if they are a veterinarian)
        """
        veterinarian = data.get('veterinarian')
        appointment = data.get('appointment')
        patient = self.context['request'].user
        
        # Check if patient is reviewing themselves
        if hasattr(patient, 'vet_profile') and patient.veterinarian_profile.id == veterinarian.id:
            raise serializers.ValidationError("Veterinarians cannot review themselves.")
        
        # Check if appointment belongs to the patient and veterinarian
        if appointment.pet_owner != patient:
            raise serializers.ValidationError("You can only review appointments you booked.")
        
        if appointment.veterinarian != veterinarian:
            raise serializers.ValidationError("This appointment is not with the specified veterinarian.")
        
        # Check if appointment is completed
        if appointment.status != 'COMPLETED':
            raise serializers.ValidationError("You can only review completed appointments.")
        
        return data

