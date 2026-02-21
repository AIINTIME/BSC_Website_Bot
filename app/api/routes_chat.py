# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.services.retrieval_service import retrieve_relevant_faqs
# from app.services.rag_service import generate_answer

# router = APIRouter()

# class ChatRequest(BaseModel):
#     message: str

# class ChatResponse(BaseModel):
#     answer: str
#     confidence: float

# @router.post("/chat", response_model=ChatResponse)
# def chat(request: ChatRequest):
#     matches, score = retrieve_relevant_faqs(request.message)

#     if not matches:
#         return ChatResponse(
#             answer="I do not have that information in the official FAQs. Please contact the admissions office.",
#             confidence=score
#         )

#     answer = generate_answer(request.message, matches)
#     print("\n[GENERATION DEBUG]")
#     print("Query:", request.message)
#     print("Answer:", answer)
#     print("Confidence:", score)
#     return ChatResponse(
#         answer=answer,
#         confidence=score
#     )

# Rewrite
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.rag_pipeline import run_rag
from app.services.memory_store_redis import append_turn

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/chat")
def chat(req: ChatRequest):
    result = run_rag(req.message, session_id=req.session_id)
    # append_turn(req.session_id or "", req.message, result["answer"])
    return result


