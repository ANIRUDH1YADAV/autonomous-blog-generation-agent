from fastapi import APIRouter
from pydantic import BaseModel
from app.services.llm_service import generate_text

router = APIRouter()


class BlogRequest(BaseModel):
    topic: str


@router.post("/generate_blog")
def generate_blog(request: BlogRequest):
    prompt = f"Write a professional blog introduction about {request.topic}."

    blog_intro = generate_text(prompt)

    return {
        "topic": request.topic,
        "introduction": blog_intro
    }