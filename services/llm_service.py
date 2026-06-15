"""
Groq API integration for the VetAI chatbot.
Uses Llama 3.3 70B for text and Llama 4 Scout (multimodal) for image+text.

Ported from FastAPI async to Django-compatible synchronous functions.
"""
import re
import uuid
import base64
from pathlib import Path
from django.conf import settings
from .disease_mapping import DISEASE_KNOWLEDGE_BASE, DISEASES

_client = None  # Groq client — lazily initialized

# Models
TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Rejection messages
REJECTION_NO_PET = (
    "I am a veterinary assistant and can only help with pet health, pet symptoms, "
    "animal diseases, pet care, and veterinary-related questions. Please describe "
    "your pet's symptoms or upload an image of your pet."
)
REJECTION_NO_SKIN = "Please upload a clearer image showing the affected skin area."

SYSTEM_PROMPT = """You are VetAI, a friendly and knowledgeable veterinary assistant. You help pet owners with health questions, symptoms, and pet care advice. You are conversational, warm, and always helpful — even when users go off-topic.

# ⛔ CRITICAL: INTERNAL REASONING IS FORBIDDEN IN OUTPUT ⛔

The sections below (marked [INTERNAL]) describe your THINKING PROCESS. They are NOT part of your response. You must NEVER output:
- Step labels like "STEP 0", "STEP 1", "STEP 2", "IMAGE VALIDATION PASSED", "CLASSIFY INTENT"
- Checkmarks, validation status, or thinking commentary
- Any meta-commentary about what step you're on
- Phrases like "Based on the image validation step" or "After classifying the intent"

Your response must go DIRECTLY to the final output — a casual reply, a friendly redirect, or a health concern analysis. Nothing else.

---

[INTERNAL — THINK SILENTLY, NEVER OUTPUT]

IMAGE VALIDATION (when an image is uploaded):

1. Does the image contain a dog, cat, or other pet animal (rabbit, bird, etc.)?
   - If NO → Your ENTIRE response must be EXACTLY: "I am a veterinary assistant and can only help with pet health, pet symptoms, animal diseases, pet care, and veterinary-related questions. Please describe your pet's symptoms or upload an image of your pet."
   - Do NOT describe the image. Do NOT make a joke. Do NOT add anything else.

2. If a pet IS present, is the skin/fur/affected area clearly visible?
   - If NOT clearly visible → Your ENTIRE response must be EXACTLY: "Please upload a clearer image showing the affected skin area."

3. Only proceed if BOTH: pet clearly present AND skin/affected area clearly visible.

INTENT CLASSIFICATION:

- OFF-TOPIC TEXT — message has nothing to do with pets, animals, or veterinary topics. Examples: "yeh chair kaisi hai", "what's the weather like", "tell me a recipe".
- JOKE / SARCASM / PLAYFUL — pet-related humor. Examples: "my goldfish has anxiety", "my cat is plotting to kill me".
- GENERAL CHAT — casual pet-related conversation. Examples: "hello", "tell me a fun fact about dogs", "what breed is best for apartments", "okay thanks".
- GENUINE HEALTH CONCERN — symptoms described or validated pet image uploaded.

[/INTERNAL]

---

RESPOND DIRECTLY — pick ONE of the modes below:

### IF REJECTING AN IMAGE:
Respond with EXACTLY the rejection message and nothing else. This rule applies ONLY to uploaded images — never use the rejection message for text-only messages.

### IF OFF-TOPIC TEXT (text only, no image):
The user said something completely unrelated to pets or animals. Respond naturally and briefly — acknowledge their message in a friendly way, then gently steer back to pet health. Keep it to 1-2 sentences. Be warm, not robotic. Vary your responses — NEVER repeat the same redirection message.

Examples of good off-topic responses:
- "That's an interesting question! While I'm not the best assistant for that, I'm here whenever you have questions about your pet's health. 🐾"
- "I'm not much help with that topic, but if your pet is showing any symptoms or you need care advice, I'd love to help!"
- "I focus on pet health, so I can't help much with that one. Is there anything about your pet you'd like to discuss?"

⛔ CRITICAL: For off-topic TEXT messages, NEVER use the image rejection message ("I am a veterinary assistant and can only help with pet health..."). That message is ONLY for non-pet IMAGES. Using it for text messages makes you sound broken.

### IF JOKE / SARCASM / PLAYFUL (text only, never images):
Play along. Keep it short — 1 to 3 lines max. No medical advice.

### IF GENERAL CHAT:
Be friendly and conversational. Answer naturally. No medical structure. This includes greetings, thank-yous, follow-ups, and casual pet questions. Match the user's tone.

### IF GENUINE HEALTH CONCERN:
Act as a knowledgeable veterinary assistant. Rules:

1. ⚠️ You are NOT a replacement for a licensed veterinarian. No generic disclaimer — the UI handles that.
2. If symptoms suggest an emergency (difficulty breathing, seizures, severe bleeding, collapse, inability to urinate, distended/bloated abdomen, paralysis), flag it IMMEDIATELY.
3. 🚫 BIOLOGICAL REALITY CHECK — correct biologically impossible claims. Examples: rabbits cannot vomit, horses cannot vomit, cats are obligate carnivores, birds excrete urates with feces, rats/mice/guinea pigs cannot vomit.
4. Ask 2-3 clarifying questions before giving advice.
5. When an image was uploaded, weave observations naturally into your explanation — no separate "Image Observations" heading.
6. Be specific — name actual conditions.
7. Focus on the most likely issue.

RESPONSE FORMAT (health concern only):

🐾 Possible Issue: [1-2 sentences in plain language]

💊 What You Can Do:
• [Actionable step 1]
• [Actionable step 2]
• [Actionable step 3]

🏥 When to See a Vet: [One short sentence]

🛡️ Prevention Tips: [One short sentence or two brief bullets]

FORMAT RULES:
- NEVER output: "STEP", "IMAGE VALIDATION", "INTENT", "CLASSIFY", validation checkmarks, or thinking commentary.
- NEVER use: "Image Observations", "Likely Condition", "Confidence", "Differential Diagnoses", "Key Symptoms", "Home Care", "Image Analysis", "Diagnosis", "Prognosis".
- NEVER mention confidence percentages or scores.
- NEVER use markdown headings (##, ###).
- Each label (🐾, 💊, 🏥, 🛡️) appears ONCE only.
- Use • bullet points for lists.

LANGUAGE: Match the user's language (English, Roman Urdu, or Urdu script).

DISEASES YOU COVER (in detail):
{disease_knowledge}

GUARDRAILS:
- 🚨 For non-pet IMAGES only: respond with EXACTLY the rejection message. Never use this rejection for text.
- 🚨 REJECT unclear pet images with EXACTLY: "Please upload a clearer image showing the affected skin area."
- For off-topic TEXT: respond naturally and briefly, then gently redirect. Vary your wording each time. Never repeat the same message.
- NEVER output your internal thinking/steps/validation process.
- NEVER describe furniture, people, cars, landscapes, or any non-pet object in an uploaded image.
- When in doubt about an image → REJECT it.
- When in doubt about text → treat it as GENERAL CHAT and respond conversationally.
"""


def _get_client():
    """Get or create the Groq client instance. Lazily imports Groq."""
    global _client
    if _client is None:
        from groq import Groq
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
            raise ValueError("GROQ_API_KEY is not configured. Set it in .env")
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _build_system_prompt() -> str:
    """Build the system prompt with disease knowledge."""
    kb_parts = []
    for disease in DISEASES:
        info = DISEASE_KNOWLEDGE_BASE[disease]
        kb_parts.append(
            f"### {disease}\n"
            f"- Common in: {info['common_in']}\n"
            f"- Key symptoms: {', '.join(info['symptoms'])}\n"
            f"- Typical treatments: {', '.join(info['treatments'])}\n"
            f"- When to see vet: {info['vet_urgency']}"
        )
    return SYSTEM_PROMPT.format(disease_knowledge="\n\n".join(kb_parts))


def _encode_image_to_base64(image_path: str) -> str:
    """Read an image file and return a base64 data URI."""
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"


def validate_pet_image(image_path: str) -> tuple[bool, str | None]:
    """
    Pre-check: does this image contain a pet animal with visible skin/fur?

    Uses a minimal Groq vision call (max_tokens=5, temperature=0) as a fast
    gatekeeper BEFORE the main conversational LLM call.

    Returns:
        (is_valid, rejection_message)
        - (True, None)  → animal with visible skin/fur detected, proceed
        - (False, msg)  → no animal or unclear, reject immediately
    """
    try:
        client = _get_client()
        image_uri = _encode_image_to_base64(image_path)

        completion = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Look at this image. Is there a dog, cat, or other pet animal "
                            "(rabbit, bird, etc.) with visible skin or fur in this image? "
                            "Answer ONLY 'YES' or 'NO'. Do not say anything else."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": image_uri}},
                ],
            }],
            temperature=0,
            max_tokens=5,
        )

        answer = completion.choices[0].message.content.strip().upper()
        if answer.startswith("YES"):
            return True, None
        else:
            return False, REJECTION_NO_PET

    except Exception as e:
        print(f"[validate_pet_image] Validation call failed, allowing through: {e}")
        return True, None


def stream_chat_response(
    session,
    history: list[dict],
    user_message: str,
    image_analysis: dict | None = None,
    image_path: str | None = None,
):
    """
    Stream the Groq response — yields text chunks as they arrive.
    Synchronous generator function for Django SSE.
    """
    client = _get_client()
    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    # RAG context
    try:
        from services.rag_service import query_pgvector, format_rag_context
        retrieved = query_pgvector(user_message, top_k=5)
        rag_context = format_rag_context(retrieved)
        if rag_context:
            messages.append({
                "role": "system",
                "content": "Reference data:\n\n" + rag_context,
            })
    except Exception:
        pass

    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    if image_path:
        try:
            image_uri = _encode_image_to_base64(image_path)
            validation_text = (
                "⚠️ IMAGE ATTACHED — VALIDATE FIRST:\n"
                "Before anything else, check: does this image contain a pet animal "
                "(dog, cat, rabbit, bird) with visible skin or fur?\n"
                "→ If NO animal is present: respond ONLY with \"I am a veterinary assistant "
                "and can only help with pet health, pet symptoms, animal diseases, pet care, "
                "and veterinary-related questions. Please describe your pet's symptoms or "
                "upload an image of your pet.\"\n"
                "→ If animal present but skin/fur NOT clearly visible: respond ONLY with "
                "\"Please upload a clearer image showing the affected skin area.\"\n"
                "→ ONLY if a pet with visible skin/fur is clearly present, proceed with analysis.\n"
                "DO NOT describe chairs, furniture, people, cars, landscapes, or any non-pet object.\n\n"
            )
            user_text = validation_text + (user_message or "Please analyze this pet image.")
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_uri}},
            ]
            messages.append({"role": "user", "content": user_content})
            model = VISION_MODEL
            max_t = max(settings.LLM_MAX_TOKENS, 4096)
        except Exception:
            messages.append({"role": "user", "content": user_message})
            model = TEXT_MODEL
            max_t = settings.LLM_MAX_TOKENS
    else:
        augmented = user_message
        if image_analysis:
            augmented = (
                f"{user_message}\n\n"
                f"[The uploaded image appears to show signs of {image_analysis['disease']}. "
                f"Use this as a reference point but make your own assessment based on what you see.]"
            )
        messages.append({"role": "user", "content": augmented})
        model = TEXT_MODEL
        max_t = settings.LLM_MAX_TOKENS

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=max_t,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def get_chat_response(
    session,
    history: list[dict],
    user_message: str,
    image_analysis: dict | None = None,
    image_path: str | None = None,
) -> str:
    """
    Send the conversation to Groq and return the assistant's response.
    Synchronous version for Django compatibility.
    """
    client = _get_client()
    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    # RAG context
    try:
        from services.rag_service import query_pgvector, format_rag_context
        retrieved = query_pgvector(user_message, top_k=5)
        rag_context = format_rag_context(retrieved)
        if rag_context:
            messages.append({
                "role": "system",
                "content": (
                    "Use the following reference data from our veterinary database "
                    "to inform your answer. Base your diagnosis and treatment "
                    "recommendations on these verified sources:\n\n" + rag_context
                ),
            })
    except Exception:
        pass

    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    if image_path:
        try:
            image_uri = _encode_image_to_base64(image_path)
            validation_text = (
                "⚠️ IMAGE ATTACHED — VALIDATE FIRST:\n"
                "Before anything else, check: does this image contain a pet animal "
                "(dog, cat, rabbit, bird) with visible skin or fur?\n"
                "→ If NO animal is present: respond ONLY with \"I am a veterinary assistant "
                "and can only help with pet health, pet symptoms, animal diseases, pet care, "
                "and veterinary-related questions. Please describe your pet's symptoms or "
                "upload an image of your pet.\"\n"
                "→ If animal present but skin/fur NOT clearly visible: respond ONLY with "
                "\"Please upload a clearer image showing the affected skin area.\"\n"
                "→ ONLY if a pet with visible skin/fur is clearly present, proceed with analysis.\n"
                "DO NOT describe chairs, furniture, people, cars, landscapes, or any non-pet object.\n\n"
            )
            user_text = validation_text + (user_message or "Please analyze this pet image.")
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_uri}},
            ]
            messages.append({"role": "user", "content": user_content})
            model = VISION_MODEL
        except Exception:
            messages.append({"role": "user", "content": user_message})
            model = TEXT_MODEL
    else:
        augmented_message = user_message
        if image_analysis:
            augmented_message = (
                f"{user_message}\n\n"
                f"[The uploaded image appears to show signs of {image_analysis['disease']}. "
                f"Use this as a reference point but make your own assessment based on what you see.]"
            )
        messages.append({"role": "user", "content": augmented_message})
        model = TEXT_MODEL

    max_tokens = settings.LLM_MAX_TOKENS if not image_path else max(settings.LLM_MAX_TOKENS, 4096)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=max_tokens,
    )

    return completion.choices[0].message.content


def parse_diagnosis_from_response(response_text: str, session_id: uuid.UUID) -> dict | None:
    """
    Parse the structured diagnosis from the LLM response.
    Returns a dict matching the Diagnosis model if a diagnosis was found.
    """
    diagnosis = {
        "session_id": session_id,
        "disease": "Pet Health Concern",
        "confidence": None,
        "symptoms_summary": None,
        "treatment_plan": None,
    }

    has_new_format = "🐾 Possible Issue:" in response_text
    has_old_format = "**Likely Condition:**" in response_text

    if not has_new_format and not has_old_format:
        return None

    if has_new_format:
        disease_match = re.search(
            r'(?:\*\*)?🐾\s*Possible Issue:(?:\*\*)?\s*(.+?)(?:\n(?:\*\*)?[💊🏥🛡️]|\n\n|$)',
            response_text, re.DOTALL
        )
        if disease_match:
            full_text = disease_match.group(1).strip()
            first_sentence = re.split(r'[.!?]\s+', full_text)[0].strip()
            disease_name = first_sentence if len(first_sentence) <= 80 else first_sentence[:80] + "..."
            diagnosis["disease"] = disease_name
            diagnosis["symptoms_summary"] = full_text

        what_to_do_match = re.search(
            r'(?:\*\*)?💊\s*What You Can Do:(?:\*\*)?\s*(.+?)(?:\n(?:\*\*)?[🏥🛡️]|\n\n|$)',
            response_text, re.DOTALL
        )
        treatment_parts = []
        if what_to_do_match:
            treatment_parts.append(what_to_do_match.group(1).strip())

        vet_match = re.search(
            r'(?:\*\*)?🏥\s*When to See a Vet:(?:\*\*)?\s*(.+?)(?:\n(?:\*\*)?[🛡️]|\n\n|$)',
            response_text, re.DOTALL
        )
        if vet_match:
            treatment_parts.append("When to See a Vet: " + vet_match.group(1).strip())

        prevention_match = re.search(
            r'(?:\*\*)?🛡️\s*Prevention Tips:(?:\*\*)?\s*(.+?)(?:\n\n|$)',
            response_text, re.DOTALL
        )
        if prevention_match:
            treatment_parts.append("Prevention: " + prevention_match.group(1).strip())

        if treatment_parts:
            diagnosis["treatment_plan"] = "\n\n".join(treatment_parts)

        return diagnosis

    # Old format (backward compatibility)
    disease_match = re.search(r'\*\*Likely Condition:\*\*\s*(.+?)(?:\n|$)', response_text)
    if disease_match:
        diagnosis["disease"] = disease_match.group(1).strip()

    conf_match = re.search(r'\*\*Confidence:\*\*\s*(.+?)(?:\n|$)', response_text)
    if conf_match:
        conf_text = conf_match.group(1).strip().lower()
        if "high" in conf_text:
            diagnosis["confidence"] = 0.85
        elif "medium" in conf_text:
            diagnosis["confidence"] = 0.60
        elif "low" in conf_text:
            diagnosis["confidence"] = 0.35

    sym_match = re.search(r'\*\*Symptoms You Described:\*\*\s*(.+?)(?:\n\*\*|\n\n)', response_text, re.DOTALL)
    if sym_match:
        diagnosis["symptoms_summary"] = sym_match.group(1).strip()

    treatment_parts = []
    home_care = re.search(r'\*\*Home Care:\*\*\s*(.+?)(?:\n\*\*|\n\n)', response_text, re.DOTALL)
    if home_care:
        treatment_parts.append(f"Home Care:\n{home_care.group(1).strip()}")

    vet_visit = re.search(r'\*\*When to See a Vet:\*\*\s*(.+?)(?:\n\*\*|\n\n|$)', response_text, re.DOTALL)
    if vet_visit:
        treatment_parts.append(f"When to See a Vet:\n{vet_visit.group(1).strip()}")

    prevention = re.search(r'\*\*Prevention Tips:\*\*\s*(.+?)(?:\n\*\*|\n\n|$)', response_text, re.DOTALL)
    if prevention:
        treatment_parts.append(f"Prevention:\n{prevention.group(1).strip()}")

    if treatment_parts:
        diagnosis["treatment_plan"] = "\n\n".join(treatment_parts)

    return diagnosis
