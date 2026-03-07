from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3
    )