import time
from functools import lru_cache

from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.config import get_settings


class MissingApiKey(RuntimeError):
    pass


@lru_cache
def get_pinecone() -> Pinecone:
    settings = get_settings()
    if not settings.pinecone_api_key:
        raise MissingApiKey("PINECONE_API_KEY is not set in backend/.env")
    return Pinecone(api_key=settings.pinecone_api_key)


@lru_cache
def get_index():
    """Return the Pinecone index, creating it on first use."""
    settings = get_settings()
    pc = get_pinecone()
    if not pc.has_index(settings.pinecone_index):
        pc.create_index(
            name=settings.pinecone_index,
            dimension=settings.embedding_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
        while not pc.describe_index(settings.pinecone_index).status["ready"]:
            time.sleep(1)
    return pc.Index(settings.pinecone_index)


@lru_cache
def get_embeddings() -> PineconeEmbeddings:
    settings = get_settings()
    get_pinecone()  # fail fast with a clear message when the key is missing
    return PineconeEmbeddings(
        model=settings.embedding_model,
        dimension=settings.embedding_dim,
        pinecone_api_key=settings.pinecone_api_key,
    )


@lru_cache
def get_vectorstore() -> PineconeVectorStore:
    settings = get_settings()
    return PineconeVectorStore(
        index=get_index(),
        embedding=get_embeddings(),
        namespace=settings.pinecone_namespace,
    )


def delete_document_vectors(doc_id: str) -> None:
    index = get_index()
    namespace = get_settings().pinecone_namespace
    for ids in index.list(prefix=f"{doc_id}#", namespace=namespace):
        if ids:
            index.delete(ids=ids, namespace=namespace)


def namespace_vector_count() -> int:
    stats = get_index().describe_index_stats()
    ns = stats.namespaces.get(get_settings().pinecone_namespace)
    return ns.vector_count if ns else 0
