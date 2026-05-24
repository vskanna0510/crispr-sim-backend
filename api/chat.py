"""RAG chatbot API — project help grounded in knowledge/*.md."""

from fastapi import APIRouter, HTTPException

from models.schemas import RAGChatRequest, RAGChatResponse
from services.rag_service import rag_answer

router = APIRouter(prefix="/chat", tags=["RAG Chat"])


@router.post("/rag", response_model=RAGChatResponse, summary="Ask the CRISPR-Sim assistant")
async def chat_rag(body: RAGChatRequest) -> RAGChatResponse:
    try:
        answer, sources = await rag_answer(body.message, top_k=body.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return RAGChatResponse(answer=answer, sources=sources)
