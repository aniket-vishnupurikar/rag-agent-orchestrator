from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()


from src.api.chat.chat_routes import router as chat_router

app = FastAPI(
    title="Agentic Chat Service",
    version="1.0.0"
)

# Register chat routes
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
