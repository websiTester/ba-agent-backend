from fastapi import APIRouter
from pydantic import BaseModel

from services.chunk_and_embedding import chunk_and_embedding, delete_chunk
from services.get_relevant_context import get_relevant_context


router = APIRouter()

class ChunkAndEmbeddingRequest(BaseModel):
    document: str
    source: str
    phaseId: str


class DeleteChunkRequest(BaseModel):
    phaseId: str
    source: str


@router.post("/chunk_and_embedding/{phaseId}")
def chunk_and_embedding_document(request: ChunkAndEmbeddingRequest):

    return {"message": chunk_and_embedding(request.document, request.source, request.phaseId)}


@router.post("/get_relevant_context/{phaseId}")
def get_relevant_context_api(query: str, phaseId: str, source: list[str] = None):
    return {"relevant_context": get_relevant_context(query, phaseId, source)}


@router.delete("/delete_chunk")
def delete_chunk_by_filename(request: DeleteChunkRequest):
    return {"message": delete_chunk(request.phaseId, request.source)}