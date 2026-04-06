try:
    from _common import setup_path
except ImportError:
    from scripts._common import setup_path

setup_path()

from services.embedding import embed_text
from services.storage import search_similar_chunks

def main():
    query = "什麼是RAG流程？"
    query_embedding = embed_text(query)
    results = search_similar_chunks(query_embedding, top_k=3)

    for i, item in enumerate(results, 1):
        print(f"--- Top {i} ---")
        print("score:", item["score"])
        print("source:", item["source"])
        print("chunk_id:", item["chunk_id"])
        print("text:", item["text"][:200])
        print()

if __name__ == "__main__":
    main()