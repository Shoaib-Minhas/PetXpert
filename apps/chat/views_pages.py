"""
Server-rendered AI Diagnosis page view.
"""
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken


def ai_diagnosis_page(request):
    """
    Render the AI Diagnosis chat interface page.

    Note: PetXpert uses JWT stored in localStorage for auth,
    not Django sessions. The template's JS handles auth checks.
    JWT tokens are passed for the chat API to use.
    """
    context = {}

    # If user is authenticated via Django session, include JWT tokens
    if request.user.is_authenticated:
        refresh = RefreshToken.for_user(request.user)
        context["jwt_access_token"] = str(refresh.access_token)
        context["jwt_refresh_token"] = str(refresh)

    return render(request, "diagnosis/ai_diagnosis.html", context)
