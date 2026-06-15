"""
API URL patterns for chat / AI Diagnosis.
"""
from django.urls import path
from .views_api import (
    SessionListCreateView, SessionDetailView,
    MessageCreateView, MessageListView, MessageStreamView,
    DiagnosisView, HealthCheckView,
)

urlpatterns = [
    # Health
    path("health", HealthCheckView.as_view(), name="api_health"),

    # Sessions
    path("chat/sessions", SessionListCreateView.as_view(), name="api_session_list_create"),
    path("chat/sessions/<uuid:session_id>", SessionDetailView.as_view(), name="api_session_detail"),

    # Messages
    path("chat/sessions/<uuid:session_id>/messages", MessageListView.as_view(), name="api_message_list"),
    path("chat/sessions/<uuid:session_id>/messages/send", MessageCreateView.as_view(), name="api_message_send"),
    path("chat/sessions/<uuid:session_id>/messages/stream", MessageStreamView.as_view(), name="api_message_stream"),

    # Legacy aliases matching original routes
    path("chat/sessions/<uuid:session_id>/send", MessageCreateView.as_view()),
    path("chat/sessions/<uuid:session_id>/stream", MessageStreamView.as_view()),

    # Diagnosis
    path("chat/sessions/<uuid:session_id>/diagnosis", DiagnosisView.as_view(), name="api_diagnosis"),
]
