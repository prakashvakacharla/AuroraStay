"""Internal Flask API. Run from backend_files with gunicorn app:rag_api."""
import math
import os
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from rag_utils import retrieve, rag
from evaluation_utils import score_live

rag_api = Flask("AuroraStay API")
rag_api.config["MAX_CONTENT_LENGTH"] = 32 * 1024
embeddings = HuggingFaceEmbeddings(
    model_name="HarishMaths/Hotel-Policy-Embedding",
    model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True},
)
# Only load the trusted index built by this project's notebook, never user uploads.
vectorstore = FAISS.load_local(
    str(Path(__file__).parent / "faiss_index"), embeddings,
    allow_dangerous_deserialization=True,
)


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    query = data.get("query")
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 4000:
        raise ValueError("query must contain 1 to 4000 characters.")
    options = {"k": data.get("k", 3), "temperature": data.get("temperature", 0.0),
               "top_p": data.get("top_p", 1.0), "max_tokens": data.get("max_tokens", 512)}
    for name, low, high in [("k", 1, 10), ("max_tokens", 64, 2048)]:
        value = options[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an integer between {low} and {high}.")
    for name, low, high in [("temperature", 0, 1), ("top_p", 0.01, 1)]:
        value = options[name]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be a number between {low} and {high}.")
    model = data.get("model_name", "gpt-4o-mini")
    allowed = os.getenv("ALLOWED_MODELS", "gpt-4o-mini").split(",")
    if model not in allowed:
        raise ValueError("model_name is not enabled for this API.")
    return query.strip(), {**options, "model_name": model}


@rag_api.get("/")
def home():
    return jsonify({"status": "ready", "vectors": vectorstore.index.ntotal})


@rag_api.post("/v1/relevant_chunks")
@rag_api.post("/v1/answer_with_relevant_chunks")
@rag_api.post("/v1/answer")
def inference():
    try:
        query, options = validate_payload(request.get_json())
    except (ValueError, BadRequest, UnsupportedMediaType) as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        if request.path == "/v1/relevant_chunks":
            return jsonify({"query": query, "k": options["k"],
                            "relevant_chunks": retrieve(query, options["k"], vectorstore)})
        answer, chunks = rag(query, vectorstore=vectorstore, **options)
        evaluation = score_live(query, answer, chunks)
        result = {"query": query, "answer": answer, **evaluation}
        if request.path != "/v1/answer":
            result["relevant_chunks"] = chunks
        return jsonify(result)
    except Exception:
        rag_api.logger.exception("RAG request failed")
        return jsonify({"error": "Unable to complete the request; use manual lookup.",
                        "route": "MANUAL LOOKUP"}), 502


if __name__ == "__main__":
    rag_api.run(host="0.0.0.0", port=7860)
