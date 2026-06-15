"""
DRF API views for the AI Diagnosis chat system.
All business logic is delegated to the service layer.
"""
import uuid
import json
import shutil
import os
from pathlib import Path
from datetime import datetime, timezone

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from .models import Session, Message, Diagnosis
from .serializers import (
    SessionSerializer, SessionCreateSerializer, SessionListSerializer,
    MessageSerializer, MessageCreateSerializer,
    DiagnosisSerializer, ChatResponseSerializer,
)


# ── Health ──────────────────────────────────────────────────────────────────

class HealthCheckView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "VetAI",
            "version": "3.0.0",
            "framework": "Django",
        })


# ── Base chat view mixin ────────────────────────────────────────────────────

class ChatBaseView(APIView):
    """Base view that ensures user has access to the session."""

    def get_session(self, session_id: uuid.UUID) -> Session:
        """Fetch a session, ensuring it belongs to the authenticated user."""
        try:
            session = Session.objects.select_related("user").get(id=session_id)
        except Session.DoesNotExist:
            raise NotFound(detail="Session not found")
        if session.user != self.request.user:
            raise PermissionDenied(detail="Access denied to this session")
        return session


# ── Sessions ────────────────────────────────────────────────────────────────

class SessionListCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """List all sessions for the authenticated user."""
        sessions = Session.objects.filter(
            user=request.user
        ).order_by("-updated_at")[:50]
        serializer = SessionSerializer(sessions, many=True)
        return Response({"sessions": serializer.data})

    def post(self, request):
        """Create a new chat session."""
        serializer = SessionCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return Response(
            SessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(ChatBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        """Get a session by ID."""
        session = self.get_session(session_id)
        return Response(SessionSerializer(session).data)

    def delete(self, request, session_id):
        """Delete a session and its associated files."""
        session = self.get_session(session_id)

        # Clean up uploaded images
        session_dir = Path(settings.UPLOAD_DIR) / str(session.id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Messages ────────────────────────────────────────────────────────────────

class MessageListView(ChatBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        """Get all messages for a session."""
        session = self.get_session(session_id)
        messages = session.messages.all()
        return Response(MessageSerializer(messages, many=True).data)


class MessageCreateView(ChatBaseView):
    """Send a message in a session and get the AI response."""

    def post(self, request, session_id):
        session = self.get_session(session_id)

        content = request.data.get("content", "").strip()
        if not content or len(content) > 4000:
            raise ValidationError(detail={"content": "Message must be 1-4000 characters."})

        image = request.FILES.get("image")
        image_url = None
        image_abs_path = None
        image_analysis = None
        image_rejected = None

        # Handle image upload
        if image and image.name:
            image_url = self._save_image(session.id, image)
            rel_path = image_url.lstrip("/")
            image_abs_path = str(Path(settings.UPLOAD_DIR).parent / rel_path)

            # Validate: reject non-pet images
            try:
                from services.llm_service import validate_pet_image
                is_valid, rejection_msg = validate_pet_image(image_abs_path)
                if not is_valid:
                    image_rejected = rejection_msg
                else:
                    image_analysis = self._analyze_image(image_url)
            except Exception:
                # If validation service is unavailable, proceed without it
                image_analysis = self._analyze_image(image_url)

        # Save user message
        user_msg = Message.objects.create(
            session=session,
            role="user",
            content=content,
            image_url=image_url,
        )
        session.save()  # Update updated_at

        # Handle image rejection
        if image_rejected:
            assistant_msg = Message.objects.create(
                session=session,
                role="assistant",
                content=image_rejected,
            )
            return Response(ChatResponseSerializer({
                "message": assistant_msg,
                "diagnosis": None,
            }).data)

        # Get chat history
        history = self._get_chat_history(session.id)

        # Get AI response via service layer
        try:
            from services.chat_service import ChatService
            chat_service = ChatService()
            ai_text, diagnosis_data = chat_service.get_chat_response(
                session=session,
                history=history,
                user_message=content,
                image_analysis=image_analysis,
                image_path=image_abs_path,
            )
        except Exception as e:
            ai_text = f"I'm having trouble right now. Please try again. ({type(e).__name__})"
            diagnosis_data = None

        # Save assistant message
        assistant_msg = Message.objects.create(
            session=session,
            role="assistant",
            content=ai_text,
        )

        # Save diagnosis if present
        diagnosis_resp = None
        if diagnosis_data:
            diagnosis = Diagnosis.objects.create(
                session_id=session.id,
                disease=diagnosis_data.get("disease", "Unknown"),
                confidence=diagnosis_data.get("confidence"),
                symptoms_summary=diagnosis_data.get("symptoms_summary"),
                treatment_plan=diagnosis_data.get("treatment_plan"),
            )
            diagnosis_resp = DiagnosisSerializer(diagnosis).data

        return Response(ChatResponseSerializer({
            "message": assistant_msg,
            "diagnosis": diagnosis_resp,
        }).data)

    def _save_image(self, session_id: uuid.UUID, image) -> str:
        """Save an uploaded image to disk."""
        ext = os.path.splitext(image.name or "image.jpg")[1] or ".jpg"
        safe_ext = ext if ext.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
        filename = f"{uuid.uuid4().hex[:12]}{safe_ext}"
        session_dir = Path(settings.UPLOAD_DIR) / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        max_size_mb = getattr(settings, 'MAX_IMAGE_SIZE_MB', 10)
        if image.size > max_size_mb * 1024 * 1024:
            raise ValidationError(detail=f"Image exceeds {max_size_mb}MB")

        filepath = session_dir / filename
        with open(filepath, "wb+") as f:
            for chunk in image.chunks():
                f.write(chunk)

        return f"/uploads/{session_id}/{filename}"

    def _analyze_image(self, image_url: str) -> dict | None:
        """Classify a pet disease image using the ViT model."""
        try:
            from services.image_service import classify_image
            rel_path = image_url.lstrip("/")
            abs_path = Path(settings.UPLOAD_DIR).parent / rel_path
            return classify_image(str(abs_path))
        except Exception:
            return None

    def _get_chat_history(self, session_id: uuid.UUID) -> list[dict]:
        """Get chat history for the LLM context."""
        messages = Message.objects.filter(session_id=session_id).order_by("created_at")
        return [{"role": m.role, "content": m.content} for m in messages]


class MessageStreamView(ChatBaseView):
    """
    SSE streaming endpoint for real-time chat responses.
    Uses Django's StreamingHttpResponse for Server-Sent Events.
    """

    def post(self, request, session_id):
        session = self.get_session(session_id)

        content = request.data.get("content", "").strip()
        if not content or len(content) > 4000:
            raise ValidationError(detail={"content": "Message must be 1-4000 characters."})

        image = request.FILES.get("image")
        image_url = None
        image_abs_path = None
        image_rejected = None

        # Handle image
        if image and image.name:
            image_url = self._save_image(session, image)
            rel_path = image_url.lstrip("/")
            image_abs_path = str(Path(settings.UPLOAD_DIR).parent / rel_path)

            try:
                from services.llm_service import validate_pet_image
                is_valid, rejection_msg = validate_pet_image(image_abs_path)
                if not is_valid:
                    image_rejected = rejection_msg
            except Exception:
                pass  # Proceed without validation if service unavailable

        # Save user message
        Message.objects.create(
            session=session,
            role="user",
            content=content,
            image_url=image_url,
        )
        session.save()

        # Handle image rejection stream
        if image_rejected:
            return self._build_rejection_stream(session.id, image_rejected)

        history = self._get_chat_history(session.id)

        def event_generator():
            full_response = ""
            try:
                from services.llm_service import stream_chat_response
                for token in stream_chat_response(
                    session=session,
                    history=history,
                    user_message=content,
                    image_path=image_abs_path,
                ):
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            # Save assistant message after streaming completes
            if full_response.strip():
                try:
                    Message.objects.create(
                        session_id=session.id,
                        role="assistant",
                        content=full_response,
                    )
                    from services.llm_service import parse_diagnosis_from_response
                    diagnosis_data = parse_diagnosis_from_response(full_response, session.id)
                    if diagnosis_data:
                        Diagnosis.objects.create(**diagnosis_data)
                except Exception:
                    pass

            yield f"data: {json.dumps({'done': True})}\n\n"

        response = StreamingHttpResponse(
            event_generator(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _build_rejection_stream(self, session_id: uuid.UUID, message: str):
        """Return SSE stream for image rejection."""
        def rejection_generator():
            for char in message:
                yield f"data: {json.dumps({'token': char})}\n\n"
            try:
                Message.objects.create(
                    session_id=session_id,
                    role="assistant",
                    content=message,
                )
            except Exception:
                pass
            yield f"data: {json.dumps({'done': True})}\n\n"

        response = StreamingHttpResponse(
            rejection_generator(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _save_image(self, session, image) -> str:
        """Save an uploaded image to disk (instance method version)."""
        ext = os.path.splitext(image.name or "image.jpg")[1] or ".jpg"
        safe_ext = ext if ext.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
        filename = f"{uuid.uuid4().hex[:12]}{safe_ext}"
        session_dir = Path(settings.UPLOAD_DIR) / str(session.id)
        session_dir.mkdir(parents=True, exist_ok=True)

        max_size_mb = getattr(settings, 'MAX_IMAGE_SIZE_MB', 10)
        if image.size > max_size_mb * 1024 * 1024:
            raise ValidationError(detail=f"Image exceeds {max_size_mb}MB")

        filepath = session_dir / filename
        with open(filepath, "wb+") as f:
            for chunk in image.chunks():
                f.write(chunk)

        return f"/uploads/{session.id}/{filename}"

    def _get_chat_history(self, session_id: uuid.UUID) -> list[dict]:
        messages = Message.objects.filter(session_id=session_id).order_by("created_at")
        return [{"role": m.role, "content": m.content} for m in messages]


# ── Diagnosis ────────────────────────────────────────────────────────────────

class DiagnosisView(ChatBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        """Get the latest diagnosis for a session."""
        session = self.get_session(session_id)
        diagnosis = session.diagnoses.first()
        if not diagnosis:
            raise NotFound(detail="No diagnosis found for this session")
        return Response(DiagnosisSerializer(diagnosis).data)
