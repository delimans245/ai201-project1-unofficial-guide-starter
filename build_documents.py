from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
SOURCE_TEXT_DIR = DOCUMENTS_DIR / "source_texts"
RAW_DIR = DOCUMENTS_DIR / "raw"
CLEAN_DIR = DOCUMENTS_DIR / "clean"
CHUNKS_PATH = DOCUMENTS_DIR / "chunks.jsonl"

CHUNK_SIZE = 50
OVERLAP = 15
RANDOM_SEED = 42
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

SOURCE_DOCUMENTS = [
    {
        "title": "UC Berkeley Off-Campus Rental Services",
        "url": "https://och.berkeley.edu/",
        "path": SOURCE_TEXT_DIR / "uc-berkeley-off-campus-rental-services.txt",
    },
    {
        "title": "Avoid Scams & Fraud",
        "url": "https://och.berkeley.edu/avoid-scams-and-fraud",
        "path": SOURCE_TEXT_DIR / "avoid-scams-and-fraud.txt",
    },
    {
        "title": "Contact Cal Rentals",
        "url": "https://och.berkeley.edu/resources/article/5422-contact-calrentals",
        "path": SOURCE_TEXT_DIR / "contact-cal-rentals.txt",
    },
    {
        "title": "Berkeley Rent Board home page",
        "url": "https://rentboard.berkeleyca.gov/",
        "path": SOURCE_TEXT_DIR / "berkeley-rent-board-home-page.txt",
    },
    {
        "title": "Berkeley Rent Board registration page",
        "url": "https://rentboard.berkeleyca.gov/rights-responsibilities/registration",
        "path": SOURCE_TEXT_DIR / "berkeley-rent-board-registration-page.txt",
    },
    {
        "title": "Berkeley Student Cooperative home page",
        "url": "https://bsc.coop/",
        "path": SOURCE_TEXT_DIR / "berkeley-student-cooperative-home-page.txt",
    },
    {
        "title": "BSC Our Houses & Apartments",
        "url": "https://bsc.coop/housing/our-houses-apartments",
        "path": SOURCE_TEXT_DIR / "bsc-our-houses-apartments.txt",
    },
    {
        "title": "BSC Academic Year Rates",
        "url": "https://bsc.coop/housing/academic-year-rates",
        "path": SOURCE_TEXT_DIR / "bsc-academic-year-rates.txt",
    },
    {
        "title": "Apartment List Berkeley city page",
        "url": "https://www.apartmentlist.com/ca/berkeley",
        "path": SOURCE_TEXT_DIR / "apartment-list-berkeley-city-page.txt",
    },
    {
        "title": "Apartment List Downtown Berkeley page",
        "url": "https://www.apartmentlist.com/ca/berkeley/neighborhoods/downtown-berkeley",
        "path": SOURCE_TEXT_DIR / "apartment-list-downtown-berkeley-page.txt",
    },
    {
        "title": "Apartment List Southside page",
        "url": "https://www.apartmentlist.com/ca/berkeley/neighborhoods/southside",
        "path": SOURCE_TEXT_DIR / "apartment-list-southside-page.txt",
    },
    {
        "title": "Apartment List West Berkeley page",
        "url": "https://www.apartmentlist.com/ca/berkeley/neighborhoods/west-berkeley",
        "path": SOURCE_TEXT_DIR / "apartment-list-west-berkeley-page.txt",
    },
]

BOILERPLATE_LINE_PATTERNS = [
    r"^skip to content$",
    r"^skip to main content$",
    r"^cookie settings$",
    r"^accept all$",
    r"^deny all$",
    r"^we use a selection of our own and third-party cookies.*$",
    r"^powered by google translate.*$",
    r"^site map$",
    r"^sitemap$",
    r"^search website$",
    r"^search search toggle navigation$",
    r"^quick links$",
    r"^additional links$",
    r"^read more$",
    r"^read more about.*$",
    r"^view all rentals.*$",
    r"^more rental options$",
    r"^filters$",
    r"^verified listing verified.*$",
    r"^quick view.*$",
    r"^check availability$",
    r"^cookie documentation$",
    r"^the university and off campus partners.*$",
    r"^all rights reserved\.?$",
]

TAG_DROP_NAMES = {
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "button",
    "input",
    "select",
    "textarea",
    "figure",
    "figcaption",
    "template",
}

DROP_CLASS_ID_PATTERNS = [
    r"cookie",
    r"banner",
    r"header",
    r"footer",
    r"nav",
    r"breadcrumb",
    r"share",
    r"social",
    r"promo",
    r"advert",
    r"ad-",
    r"modal",
    r"popup",
    r"consent",
    r"subscribe",
    r"newsletter",
]


@dataclass
class DocumentRecord:
    title: str
    url: str
    slug: str
    raw_path: str
    clean_path: str
    raw_text: str
    clean_text: str


@dataclass
class ChunkRecord:
    chunk_id: str
    document_slug: str
    document_title: str
    source_url: str
    chunk_index: int
    token_count: int
    text: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "document"


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = [line for line in lines if line]
    return "\n".join(cleaned_lines).strip()
def clean_text(text: str) -> str:
    lines = []
    previous_line = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        normalized = re.sub(r"\s+", " ", line).strip().lower()
        if any(re.match(pattern, normalized) for pattern in BOILERPLATE_LINE_PATTERNS):
            continue

        if normalized == previous_line:
            continue

        lines.append(line)
        previous_line = normalized

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def split_sentences(text: str) -> list[str]:
    text = text.replace("\n", " ")
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def split_long_sentence(sentence: str, chunk_size: int, overlap: int) -> list[str]:
    words = sentence.split()
    if not words:
        return []

    if len(words) <= chunk_size:
        return [sentence.strip()]

    step = max(chunk_size - overlap, 1)
    pieces = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        piece = " ".join(words[start:end]).strip()
        if piece:
            pieces.append(piece)
        if end >= len(words):
            break
        start += step
    return pieces


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    if not text.strip():
        return []

    sentences: list[str] = []
    for sentence in split_sentences(text):
        if token_count(sentence) > chunk_size:
            sentences.extend(split_long_sentence(sentence, chunk_size, overlap))
        else:
            sentences.append(sentence)

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    def emit_current_chunk() -> None:
        nonlocal current_sentences, current_tokens
        if not current_sentences:
            return

        chunk_text_value = " ".join(current_sentences).strip()
        if chunk_text_value:
            chunks.append(chunk_text_value)

        if overlap <= 0:
            current_sentences = []
            current_tokens = 0
            return

        overlap_sentences: list[str] = []
        overlap_tokens = 0
        for sentence in reversed(current_sentences):
            sentence_tokens = token_count(sentence)
            if overlap_sentences and overlap_tokens + sentence_tokens > overlap:
                break
            overlap_sentences.insert(0, sentence)
            overlap_tokens += sentence_tokens
            if overlap_tokens >= overlap:
                break

        current_sentences = overlap_sentences
        current_tokens = token_count(" ".join(current_sentences))

    for sentence in sentences:
        sentence_tokens = token_count(sentence)
        if current_sentences and current_tokens + sentence_tokens > chunk_size:
            emit_current_chunk()

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    emit_current_chunk()
    return [chunk for chunk in chunks if chunk.strip()]


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def prepare_documents() -> list[DocumentRecord]:
    SOURCE_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    documents: list[DocumentRecord] = []
    for source in SOURCE_DOCUMENTS:
        slug = slugify(source["title"])
        raw_path = RAW_DIR / f"{slug}.txt"
        clean_path = CLEAN_DIR / f"{slug}.txt"

        source_path = Path(source["path"])
        if not source_path.exists():
            raise FileNotFoundError(
                f"Missing source text file: {source_path}. Create it before running the pipeline."
            )

        raw_text = normalize_whitespace(source_path.read_text(encoding="utf-8"))
        clean = clean_text(raw_text)

        save_text(raw_path, raw_text)
        save_text(clean_path, clean)

        documents.append(
            DocumentRecord(
                title=source["title"],
                url=source["url"],
                slug=slug,
                raw_path=str(raw_path.relative_to(BASE_DIR)),
                clean_path=str(clean_path.relative_to(BASE_DIR)),
                raw_text=raw_text,
                clean_text=clean,
            )
        )

    return documents


def build_chunks(documents: Iterable[DocumentRecord]) -> list[ChunkRecord]:
    chunk_records: list[ChunkRecord] = []
    for document in documents:
        chunk_texts = chunk_text(document.clean_text)
        for index, text in enumerate(chunk_texts):
            chunk_records.append(
                ChunkRecord(
                    chunk_id=f"{document.slug}-{index:03d}",
                    document_slug=document.slug,
                    document_title=document.title,
                    source_url=document.url,
                    chunk_index=index,
                    token_count=token_count(text),
                    text=text,
                )
            )
    return chunk_records


def write_chunks_jsonl(chunks: Iterable[ChunkRecord]) -> None:
    with CHUNKS_PATH.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(asdict(chunk), ensure_ascii=True) + "\n")


def print_sample_document(document: DocumentRecord) -> None:
    print("\n=== Sample cleaned document ===")
    print(f"Source: {document.title}")
    print(f"URL: {document.url}")
    print(document.clean_text[:4000])


def print_sample_chunks(chunks: list[ChunkRecord], sample_size: int = 5) -> None:
    print("\n=== Chunk summary ===")
    print(f"Documents: {len(SOURCE_DOCUMENTS)}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunk size target: {CHUNK_SIZE} tokens")
    print(f"Overlap target: {OVERLAP} tokens")

    if not chunks:
        print("No chunks were produced.")
        return

    random.seed(RANDOM_SEED)
    sample_count = min(sample_size, len(chunks))
    sampled_chunks = random.sample(chunks, sample_count)

    print("\n=== Sample chunks ===")
    for chunk in sampled_chunks:
        preview = chunk.text[:700].replace("\n", " ")
        print(f"\n[{chunk.chunk_id}] {chunk.document_title} | {chunk.token_count} tokens")
        print(preview)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cleaned document text and chunks for the Berkeley housing corpus.")
    parser.add_argument("--sample-size", type=int, default=5, help="Number of random chunks to print for inspection.")
    args = parser.parse_args()

    documents = prepare_documents()
    chunks = build_chunks(documents)
    write_chunks_jsonl(chunks)

    if documents:
        print_sample_document(documents[0])

    print_sample_chunks(chunks, sample_size=args.sample_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
