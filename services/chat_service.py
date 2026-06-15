"""
Chat service orchestrator — coordinates LLM, image analysis, and RAG.
All business logic lives here; views only handle HTTP concerns.
"""
import uuid


class ChatService:
    """
    Service layer for chatbot operations.
    Decouples business logic from Django views.
    """

    def get_chat_response(
        self,
        session,
        history: list[dict],
        user_message: str,
        image_analysis: dict | None = None,
        image_path: str | None = None,
    ) -> tuple[str, dict | None]:
        """
        Process a user message and return the AI response.
        """
        from .llm_service import get_chat_response, parse_diagnosis_from_response

        try:
            text = get_chat_response(
                session=session,
                history=history,
                user_message=user_message,
                image_analysis=image_analysis,
                image_path=image_path,
            )
            diagnosis = parse_diagnosis_from_response(text, session.id)
            return text, diagnosis
        except ImportError:
            return (
                "AI service not configured. Check GROQ_API_KEY in .env.",
                None,
            )
        except ValueError as e:
            return (str(e), None)
        except Exception as e:
            return (
                f"I'm having trouble right now. Please try again. ({type(e).__name__})",
                None,
            )

    def analyze_image(self, image_path: str) -> dict | None:
        """Analyze an uploaded image using the ViT model."""
        from .image_service import classify_image
        try:
            return classify_image(image_path)
        except Exception:
            return None
