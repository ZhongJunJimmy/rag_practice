try:
    from _common import setup_path
except ImportError:
    from scripts._common import setup_path

setup_path()

from services.chunking import load_all_markdown_files
from services.embedding import embed_text
from services.storage import (
    upsert_document,
    get_existing_chunk_state,
    upsert_chunk_with_embedding,
)
import hashlib

from libs.config import DATA_DIR

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    chunks = load_all_markdown_files(DATA_DIR)

    grouped = {}
    for chunk in chunks:
        grouped.setdefault(chunk["source"], []).append(chunk)

    total = 0
    inserted_or_updated = 0
    skipped = 0

    for source, source_chunks in grouped.items():
        full_text = "\n".join(c["text"] for c in source_chunks)
        document_hash = sha256_text(full_text)

        doc_id = upsert_document(
            source_name=source,
            file_path=source,
            content_hash=document_hash,
        )

        for chunk in source_chunks:
            total += 1
            text_hash = sha256_text(chunk["text"])

            existing = get_existing_chunk_state(doc_id, chunk["chunk_id"])

            if existing and existing["text_hash"] == text_hash:
                skipped += 1
                print(f"[SKIP] unchanged chunk: {chunk['chunk_id']}")
                continue

            emb = embed_text(chunk["text"])
            upsert_chunk_with_embedding(doc_id, chunk, emb, text_hash)

            inserted_or_updated += 1
            if existing:
                print(f"[UPDATE] changed chunk: {chunk['chunk_id']}")
            else:
                print(f"[INSERT] new chunk: {chunk['chunk_id']}")

    print()
    print(f"total={total}")
    print(f"inserted_or_updated={inserted_or_updated}")
    print(f"skipped={skipped}")


if __name__ == "__main__":
    main()