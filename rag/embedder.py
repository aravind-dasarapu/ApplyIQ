"""
rag/embedder.py — Resume Embedder (RAG Step 1)
================================================
This module converts your resume text into vector embeddings
and stores them in ChromaDB for fast semantic retrieval.

How it works (step by step):
  1. Split resume text into overlapping chunks (e.g., 300 tokens each)
     → Overlap ensures context isn't lost at chunk boundaries
  2. Convert each chunk to a vector using a free local model
     → "all-MiniLM-L6-v2" maps text to a 384-dimensional vector
     → Similar text = vectors that are close together in space
  3. Store vectors + original text in ChromaDB
     → ChromaDB runs locally in a folder, no server or API needed

Why chunks instead of the whole resume?
  → Small 8k-context LLMs can't hold a full resume + job desc + instructions
  → We retrieve only the relevant parts, saving precious context tokens
"""

import re

import chromadb
from chromadb.utils import embedding_functions

from config import (
    CHROMA_COLLECTION,
    CHROMA_DB_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
)


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        # Move forward by (chunk_size - overlap) to create overlap
        start += chunk_size - overlap

    return chunks


def embed_resume(resume_text: str) -> chromadb.Collection:

    print("\n Starting resume embedding...")

    # Step 1: Chunk the resume
    chunks = chunk_text(resume_text)
    print(f" Split resume into {len(chunks)} chunks")

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    print(f"Using embedding model: {EMBEDDING_MODEL}")

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        client.delete_collection(name=CHROMA_COLLECTION)
        print(f"Cleared old ChromaDB collection: '{CHROMA_COLLECTION}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
    )

    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"chunk_index": i, "source": "resume"} for i in range(len(chunks))],
    )

    print(f" Embedded {len(chunks)} chunks into ChromaDB at '{CHROMA_DB_PATH}'")
    return collection
