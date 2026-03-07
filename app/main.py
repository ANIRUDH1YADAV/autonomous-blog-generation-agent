from fastapi import FastAPI
from app.api.blog import router as blog_router

app = FastAPI(
    title="Autonomous Blog Generation Agent",
    description="Production-grade content generation engine using LangGraph",
    version="1.0.0"
)

app.include_router(blog_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}