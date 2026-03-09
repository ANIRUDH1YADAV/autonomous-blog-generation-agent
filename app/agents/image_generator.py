import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content


def image_generator_node(state: dict):

    sections = state["plan"]["sections"]

    images = []

    os.makedirs("generated_images", exist_ok=True)

    for section in sections[:2]:   # limit images
        title = section["title"]
        prompt = f"clean technical diagram explaining {title} in transformer architecture"

        image_bytes = query({
            "inputs": prompt
        })
       
        filename = title.replace(" ", "_") + ".png"

        path = f"generated_images/{filename}"

        with open(path, "wb") as f:
            f.write(image_bytes)

        images.append({
            "section": section,
            "path": path
        })

    state["images"] = images

    return state