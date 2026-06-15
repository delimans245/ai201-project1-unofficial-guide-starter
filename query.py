from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from build_vector_store import DEFAULT_TOP_K, RetrievalResult, get_vector_store, retrieve

MODEL_NAME = "llama-3.3-70b-versatile"
NO_INFORMATION_RESPONSE = "I don't have enough information on that."
SYSTEM_PROMPT = (
    "You answer questions using only the information in the provided documents. "
    "Do not use outside knowledge or guess at missing details. "
    f"If the documents do not contain enough information to answer the question, reply exactly: {NO_INFORMATION_RESPONSE} "
    "Keep the answer concise, factual, and directly tied to the context."
)
MAX_DISTANCE_FOR_GENERATION = 0.55


def load_client() -> Groq:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add a valid key to .env before running generation."
        )
    return Groq(api_key=api_key)


def format_context(results: list[RetrievalResult]) -> str:
    sections = []
    for result in results:
        sections.append(
            "\n".join(
                [
                    f"Source: {result.document_title}",
                    f"URL: {result.source_url}",
                    f"Chunk: {result.chunk_index}",
                    result.text,
                ]
            )
        )
    return "\n\n---\n\n".join(sections)


def unique_sources(results: list[RetrievalResult]) -> list[str]:
    seen: set[tuple[str, str]] = set()
    sources: list[str] = []
    for result in results:
        key = (result.document_title, result.source_url)
        if key in seen:
            continue
        seen.add(key)
        sources.append(f"{result.document_title} - {result.source_url}")
    return sources


def should_answer_from_results(results: list[RetrievalResult]) -> bool:
    return bool(results) and results[0].distance <= MAX_DISTANCE_FOR_GENERATION


def generate_answer(question: str, context: str, client: Groq) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.0,
        max_tokens=250,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Answer the question using only the provided documents. "
                    "If the documents do not contain enough information, reply exactly with: "
                    f"{NO_INFORMATION_RESPONSE}\n\n"
                    f"Question: {question}\n\n"
                    f"Documents:\n{context}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def ask(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    collection, model, _ = get_vector_store(rebuild=False)
    results = retrieve(question, collection, model, top_k=top_k)

    if not should_answer_from_results(results):
        return {
            "answer": NO_INFORMATION_RESPONSE,
            "sources": [],
            "retrieved_chunks": results,
        }

    client = load_client()
    context = format_context(results)
    answer = generate_answer(question, context, client)
    if not answer:
        answer = NO_INFORMATION_RESPONSE

    if NO_INFORMATION_RESPONSE.lower() in answer.lower() and answer.strip() != NO_INFORMATION_RESPONSE:
        answer = NO_INFORMATION_RESPONSE

    return {
        "answer": answer,
        "sources": unique_sources(results),
        "retrieved_chunks": results,
    }
