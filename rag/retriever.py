import chromadb
from chromadb.utils import embedding_functions

from config import (
    CHROMA_COLLECTION,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    TOP_K_CHUNKS,
)


def get_collection() -> chromadb.Collection:

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client.get_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
    )


def retrieve(
    query: str, collection: chromadb.Collection = None, top_k: int = TOP_K_CHUNKS
) -> str:

    if collection is None:
        collection = get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )

    chunks = results["documents"][0]  # List of matching text chunks
    combined = "\n\n---\n\n".join(chunks)
    return combined


def retrieve_full_context(collection: chromadb.Collection = None) -> str:

    if collection is None:
        collection = get_collection()

    count = collection.count()
    results = collection.get(include=["documents"])
    chunks = results["documents"]
    return "\n\n".join(chunks)
