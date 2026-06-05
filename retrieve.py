"""Milestone 4 — Retrieval.

Given a question, embed it with the same all-MiniLM-L6-v2 model used at index
time and ask ChromaDB for the top-k most similar chunks. Each result carries its
source document so the answer can be attributed in Milestone 5.

Use as a library:
    from retrieve import retrieve
    hits = retrieve("Do students pay for the bus?", k=5)

Use from the command line:
    python retrieve.py "Which dining hall do students like?"
    python retrieve.py            # runs the 5 evaluation questions from planning.md
"""

import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).parent
DB_PATH = ROOT / "chroma_db"
COLLECTION_NAME = "ucsc_guide"
TOP_K = 5

# MUST match embed.py — query and chunks have to be embedded by the same model.
EMBEDDING_FN = embedding_functions.DefaultEmbeddingFunction()

# The 5 evaluation questions from planning.md (used when run with no argument).
EVAL_QUESTIONS = [
    "Which UCSC dining hall do students recommend most?",
    "Do UCSC students have to pay for Santa Cruz Metro buses?",
    "Where on campus is a good quiet place to study?",
    "How can I save money on textbooks at UCSC?",
    "Which residential college is known for being smaller and community-focused?",
]

# Opened once and reused across calls.
_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(DB_PATH))
        _collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=EMBEDDING_FN
        )
    return _collection


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the k chunks most similar to `query`, best match first.

    Each dict has: text, source, title, chunk_index, distance (cosine distance,
    lower = more similar), and similarity (1 - distance, higher = better).
    """
    res = _get_collection().query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "title": meta["title"],
            "chunk_index": meta["chunk_index"],
            "distance": dist,
            "similarity": 1 - dist,
        })
    return hits


def _print_hits(query: str, hits: list[dict]) -> None:
    print("=" * 80)
    print(f"Q: {query}")
    print("=" * 80)
    for i, h in enumerate(hits, 1):
        snippet = " ".join(h["text"].split())[:220]
        print(f"\n[{i}] {h['source']}  (similarity {h['similarity']:.3f})")
        print(f"    {snippet}…")
    print()


def main() -> None:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        _print_hits(query, retrieve(query))
    else:
        print("No query given — running the 5 evaluation questions.\n")
        for q in EVAL_QUESTIONS:
            _print_hits(q, retrieve(q))


if __name__ == "__main__":
    main()
