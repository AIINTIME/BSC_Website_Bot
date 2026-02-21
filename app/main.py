from fastapi import FastAPI
from app.api.routes_chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HIT AI FAQ Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hit-project.in", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

@app.get("/")
def health():
    return {"status": "HIT AI Bot Running"}