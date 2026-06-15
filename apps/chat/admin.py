from django.contrib import admin
from .models import Session, Message, Diagnosis, Treatment, Embedding


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'pet_name', 'pet_breed')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'created_at')
    list_filter = ('role', 'created_at')


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'disease', 'confidence', 'created_at')
    list_filter = ('disease', 'created_at')


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'disease', 'pet_type', 'severity')
    list_filter = ('disease', 'severity')
    search_fields = ('disease',)


@admin.register(Embedding)
class EmbeddingAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_type', 'created_at')
    list_filter = ('source_type',)
