"""Milestone 4 — Embedding + Vector Store.

Reads chunks.json, turns each chunk into a vector with the all-MiniLM-L6-v2
sentence-transformer model, and stores the text + vector + metadata in a
persistent ChromaDB collection on disk (./chroma_db).

Embedding model note:
    We use all-MiniLM-L6-v2 (384-dim) through ChromaDB's built-in embedding
    function, which runs the model via onnxruntime. This is the SAME model
    planned in planning.md; we use the ONNX build instead of the
    `sentence-transformers` package because PyTorch (which sentence-transformers
    requires) has no wheel for Python 3.13 on Intel macOS. Same model, same
    embeddings, no torch dependency.

Run:  python embed.py
Re-running rebuilds the collection from scratch (safe to run repeatedly).
"""

import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).parent
CHUNKS_PATH = ROOT / "chunks.json"
DB_PATH = ROOT / "chroma_db"

COLLECTION_NAME = "ucsc_guide"
# DefaultEmbeddingFunction == all-MiniLM-L6-v2 (ONNX, 384-dim). Defined here so
# embed.py and retrieve.py use the EXACT same model on both sides.
EMBEDDING_FN = embedding_functions.DefaultEmbeddingFunction()


def main() -> None:
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH.name}")

    # (Re)create a persistent Chroma collection using cosine distance so the
    # similarity score at query time is a cosine distance (0 = identical).
    client = chromadb.PersistentClient(path=str(DB_PATH))
    try:
        client.delete_collection(COLLECTION_NAME)  # start clean on re-run
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=EMBEDDING_FN,
        metadata={"hnsw:space": "cosine"},
    )

    # Add the chunks. We pass the raw text as `documents`; Chroma embeds each one
    # with EMBEDDING_FN and stores the vector + our metadata alongside it, so
    # retrieval can return the original chunk text and its source.
    print("Embedding + storing chunks (downloads the model on first run) ...")
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[
            {"source": c["source"], "title": c["title"], "chunk_index": c["chunk_index"]}
            for c in chunks
        ],
    )

    print(f"\nStored {collection.count()} chunks in collection '{COLLECTION_NAME}'")
    print(f"Vector store persisted at: {DB_PATH}/")


if __name__ == "__main__":
    main()
