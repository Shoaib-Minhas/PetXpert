"""
DRF serializers for chat models.
"""
from rest_framework import serializers
from .models import Session, Message, Diagnosis, Treatment


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ("pet_breed", "pet_name", "pet_age")

    def create(self, validated_data):
        user = self.context["request"].user
        return Session.objects.create(
            user=user,
            tenant_id=getattr(user, "tenant_id", None),
            **validated_data,
        )


class SessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = (
            "id", "pet_breed", "pet_name", "pet_age",
            "status", "created_at", "updated_at", "message_count",
        )

    def get_message_count(self, obj):
        return obj.messages.count()


class SessionListSerializer(serializers.Serializer):
    sessions = SessionSerializer(many=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "session_id", "role", "content", "image_url", "created_at")
        read_only_fields = fields


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=4000)
    image = serializers.ImageField(required=False, allow_null=True)


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = (
            "id", "session_id", "disease", "confidence",
            "symptoms_summary", "treatment_plan", "created_at",
        )
        read_only_fields = fields


class ChatResponseSerializer(serializers.Serializer):
    message = MessageSerializer()
    diagnosis = DiagnosisSerializer(allow_null=True)


class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = "__all__"
