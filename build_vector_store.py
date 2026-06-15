from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHUNKS_PATH = DOCUMENTS_DIR / "chunks.jsonl"
VECTOR_STORE_DIR = DOCUMENTS_DIR / "vector_store"
COLLECTION_NAME = "berkeley_housing_chunks"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5

TEST_QUERIES = [
    "What does BSC say a room-and-board house costs per semester, and what is included?",
    "Which BSC house is substance-free and academically themed?",
    "How does Apartment List describe Downtown Berkeley, and what drawback does it mention?",
]


@dataclass
class ChunkRecord:
    chunk_id: str
    document_slug: str
    document_title: str
    source_url: str
    chunk_index: int
    token_count: int
    text: str


@dataclass
class RetrievalResult:
    chunk_id: str
    document_title: str
    source_url: str
    chunk_index: int
    token_count: int
    distance: float
    text: str


def load_chunks(path: Path = CHUNKS_PATH) -> list[ChunkRecord]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing chunk file at {path}. Run build_documents.py before building the vector store."
        )

    chunks: list[ChunkRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            chunks.append(ChunkRecord(**payload))
    return chunks


def load_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def normalize_for_match(text: str) -> str:
    normalized = text.lower()
    normalized = "".join(character if character.isalnum() else " " for character in normalized)
    return " ".join(normalized.split())


def title_bonus(query: str, title: str) -> float:
    normalized_query = normalize_for_match(query)
    normalized_title = normalize_for_match(title)
    bonus = 0.0

    title_words = [word for word in normalized_title.split() if len(word) > 2]
    query_words = set(word for word in normalized_query.split() if len(word) > 2)

    overlap_count = len(set(title_words) & query_words)
    bonus += 0.02 * overlap_count

    title_tokens = normalized_title.split()
    for window_size in (2, 3):
        for start in range(0, len(title_tokens) - window_size + 1):
            phrase = " ".join(title_tokens[start : start + window_size])
            if phrase and phrase in normalized_query:
                bonus += 0.08 * window_size

    return bonus


def reset_store() -> None:
    if VECTOR_STORE_DIR.exists():
        shutil.rmtree(VECTOR_STORE_DIR)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)


def create_collection(force_rebuild: bool = True):
    if force_rebuild:
        reset_store()

    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_vector_store(force_rebuild: bool = True) -> tuple[Any, SentenceTransformer, list[ChunkRecord]]:
    chunks = load_chunks()
    model = load_model()
    collection = create_collection(force_rebuild=force_rebuild)

    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()

    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=texts,
        metadatas=[
            {
                "document_slug": chunk.document_slug,
                "document_title": chunk.document_title,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            for chunk in chunks
        ],
        embeddings=embeddings,
    )

    return collection, model, chunks


def load_vector_store() -> tuple[Any, SentenceTransformer, list[ChunkRecord]]:
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    model = load_model()
    chunks = load_chunks()
    return collection, model, chunks


def get_vector_store(rebuild: bool = False) -> tuple[Any, SentenceTransformer, list[ChunkRecord]]:
    if rebuild or not VECTOR_STORE_DIR.exists():
        return build_vector_store(force_rebuild=True)
    return load_vector_store()


def retrieve(query: str, collection: Any, model: SentenceTransformer, top_k: int = DEFAULT_TOP_K) -> list[RetrievalResult]:
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()[0]

    candidate_count = max(top_k * 3, top_k)
    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"],
    )

    candidates: list[tuple[float, RetrievalResult]] = []
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]

    for document_text, metadata, distance, chunk_id in zip(documents, metadatas, distances, response["ids"][0]):
        result = RetrievalResult(
            chunk_id=chunk_id,
            document_title=metadata["document_title"],
            source_url=metadata["source_url"],
            chunk_index=int(metadata["chunk_index"]),
            token_count=int(metadata["token_count"]),
            distance=float(distance),
            text=document_text,
        )
        adjusted_distance = result.distance - title_bonus(query, result.document_title)
        candidates.append((adjusted_distance, result))

    candidates.sort(key=lambda item: (item[0], item[1].distance, item[1].chunk_index))
    return [result for _, result in candidates[:top_k]]


def print_results(query: str, results: list[RetrievalResult]) -> None:
    print(f"\n=== Query ===\n{query}")
    for index, result in enumerate(results, start=1):
        preview = result.text[:600].replace("\n", " ")
        print(
            f"\n[{index}] {result.chunk_id} | distance={result.distance:.4f} | "
            f"{result.document_title} | chunk={result.chunk_index} | tokens={result.token_count}"
        )
        print(preview)
        print(f"Source: {result.source_url}")


def run_queries(collection: Any, model: SentenceTransformer, queries: list[str], top_k: int) -> None:
    for query in queries:
        results = retrieve(query, collection, model, top_k=top_k)
        print_results(query, results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and test a ChromaDB vector store for the Berkeley housing corpus.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve per query.")
    parser.add_argument("--query", type=str, default="", help="Run a single retrieval query against the vector store.")
    parser.add_argument("--test-queries", action="store_true", help="Run the three evaluation queries from planning.md.")
    parser.add_argument("--no-rebuild", action="store_true", help="Reuse the existing vector store instead of rebuilding it.")
    args = parser.parse_args()

    if args.no_rebuild and not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            "Vector store directory does not exist yet. Run without --no-rebuild the first time."
        )

    if args.no_rebuild:
        collection, model, chunks = load_vector_store()
    else:
        collection, model, chunks = build_vector_store(force_rebuild=True)

    print(f"Built vector store with {len(chunks)} chunks in collection '{COLLECTION_NAME}'.")

    if args.query:
        print_results(args.query, retrieve(args.query, collection, model, top_k=args.top_k))
    elif args.test_queries:
        run_queries(collection, model, TEST_QUERIES, top_k=args.top_k)
    else:
        run_queries(collection, model, TEST_QUERIES, top_k=args.top_k)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
