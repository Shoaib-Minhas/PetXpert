"""
RAG (Retrieval-Augmented Generation) service using embeddings.
SQLite-compatible — uses TF-IDF fallback when pgvector is unavailable.

Architecture:
- Primary: TF-IDF + cosine similarity (always available, no GPU needed)
- Optional: HuggingFace Optimum ONNX Runtime (all-MiniLM-L6-v2, no torch needed)
- Optional: PostgreSQL pgvector extension for production scale
"""
import json
import numpy as np
from django.db import connection
from pathlib import Path

EMBED_DIM = 384
TOP_K = 3

_embed_fn = None
_model_cache = None


def _load_tfidf():
    """Load or build a TF-IDF vectorizer on medical symptom vocabulary."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD

    seed_vocab = [
        "dog ear infection scratching discharge odor head shaking",
        "cat eye infection redness discharge squinting conjunctivitis",
        "skin rash redness itching hair loss hot spot dermatitis",
        "parasites fleas ticks worms vomiting diarrhea weight loss",
        "vomiting diarrhea appetite loss lethargy digestive issue",
        "ear mites brown discharge head tilt balance loss",
        "bacterial infection fever pus antibiotics swelling",
        "fungal ringworm circular lesions hair loss crusty skin",
        "allergy itching scratching redness inflammation dermatitis",
        "cherry eye swollen third eyelid prolapse gland",
        "cataract cloudy eye vision loss aging diabetes",
        "glaucoma eye pressure pain redness dilated pupil",
        "urinary tract infection straining blood urine frequent urination",
        "respiratory infection coughing sneezing nasal discharge",
        "wound injury bleeding cut scrape abscess swelling",
        "arthritis joint pain stiffness limping mobility senior pet",
        "anxiety stress behavior change excessive licking pacing",
        "poisoning toxin ingestion vomiting seizures drooling",
        "dehydration sunken eyes skin tent tacky gums lethargy",
        "obesity overweight diet exercise joint stress",
    ]
    vec = TfidfVectorizer(stop_words="english", max_features=500)
    vec.fit(seed_vocab)
    svd = TruncatedSVD(n_components=min(EMBED_DIM, len(seed_vocab)))
    _model_cache = (vec, svd)
    return _model_cache


def _embed_tfidf(texts: list[str]) -> np.ndarray:
    """Generate pseudo-embeddings using TF-IDF + SVD."""
    vec, svd = _load_tfidf()
    tfidf_matrix = vec.transform(texts)
    reduced = svd.fit_transform(tfidf_matrix)
    norms = np.linalg.norm(reduced, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return reduced / norms


def get_embed_fn():
    """Return the best available embedding function."""
    global _embed_fn
    if _embed_fn is not None:
        return _embed_fn

    # Default to TF-IDF (always available)
    _embed_fn = _embed_tfidf

    # Try ONNX model if available
    try:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer

        model_id = "sentence-transformers/all-MiniLM-L6-v2"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = ORTModelForFeatureExtraction.from_pretrained(
            model_id, export=False, provider="CPUExecutionProvider"
        )

        def _embed_onnx(texts):
            encoded = tokenizer(
                texts, padding=True, truncation=True, max_length=128, return_tensors="np"
            )
            outputs = model(**encoded)
            token_embeddings = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"]

            mask_expanded = np.expand_dims(attention_mask, -1)
            mask_expanded = np.broadcast_to(mask_expanded, token_embeddings.shape)
            embeddings = np.sum(token_embeddings * mask_expanded.astype(np.float32), axis=1)
            mask_sum = np.sum(mask_expanded.astype(np.float32), axis=1)
            mask_sum = np.maximum(mask_sum, 1e-9)
            embeddings = embeddings / mask_sum

            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-9)
            return embeddings / norms

        _embed_fn = _embed_onnx
    except Exception:
        pass

    return _embed_fn


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    embed_fn = get_embed_fn()
    vec = embed_fn([text])
    if vec.shape[1] < EMBED_DIM:
        padded = np.zeros((1, EMBED_DIM))
        padded[0, : vec.shape[1]] = vec[0]
        vec = padded
    elif vec.shape[1] > EMBED_DIM:
        vec = vec[:, :EMBED_DIM]
    return vec[0].tolist()


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def query_pgvector(
    query_text: str,
    top_k: int = TOP_K,
    source_filter: str | None = None,
) -> list[dict]:
    """
    Search for the most similar documents to the query.
    Works with SQLite (JSON-stored vectors) and PostgreSQL (pgvector).
    """
    from apps.chat.models import Embedding

    query_vec = embed_text(query_text)

    # Filter by source_type if specified
    qs = Embedding.objects.all()
    if source_filter:
        qs = qs.filter(source_type=source_filter)

    # Compute cosine similarity in Python (works with SQLite)
    results = []
    for emb in qs:
        try:
            stored_vec = emb.embedding
            if stored_vec:
                score = _cosine_similarity(query_vec, stored_vec)
                results.append({
                    "content": emb.content,
                    "source_type": emb.source_type,
                    "score": round(score, 4),
                    "metadata": emb.metadata,
                })
        except Exception:
            continue

    # Sort by score descending and take top_k
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def format_rag_context(results: list[dict]) -> str:
    """Format retrieved documents into a context string for the LLM prompt."""
    if not results:
        return ""

    symptoms = []
    treatments = []

    for r in results:
        if r["source_type"] == "symptom_case":
            symptoms.append(f"- {r['content']} (relevance: {r['score']:.0%})")
        elif r["source_type"] == "treatment":
            treatments.append(r["content"])

    parts = []
    if symptoms:
        parts.append("[SIMILAR CASES FROM MEDICAL DATABASE]\n" + "\n".join(symptoms))
    if treatments:
        parts.append("[REFERENCE TREATMENT PROTOCOLS]\n" + "\n\n".join(treatments))

    return "\n\n".join(parts)


def insert_embeddings_batch(documents: list[dict], source_type: str) -> int:
    """Insert multiple documents into the embeddings table."""
    from apps.chat.models import Embedding

    count = 0
    for doc in documents:
        vec = embed_text(doc["content"])
        Embedding.objects.create(
            content=doc["content"],
            embedding=vec,
            source_type=source_type,
            metadata=doc.get("metadata"),
        )
        count += 1
    return count


def get_embedding_count() -> int:
    """Return the number of documents in the embeddings table."""
    from apps.chat.models import Embedding
    return Embedding.objects.count()


def clear_embeddings(source_type: str | None = None):
    """Delete all embeddings, optionally filtered by source_type."""
    from apps.chat.models import Embedding
    qs = Embedding.objects.all()
    if source_type:
        qs = qs.filter(source_type=source_type)
    qs.delete()
