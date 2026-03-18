import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

# ✅ black-forest-labs/FLUX.1-dev — actively maintained, works on HF Inference API
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

# Absolute path — resolves correctly regardless of where streamlit is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "generated_images"))


def query(prompt: str):
    """Call HF Inference API with retry for model loading (503)."""

    payload = {"inputs": prompt}

    for attempt in range(3):   # retry up to 3 times for 503 model loading
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        print(f"Attempt {attempt + 1} | Status: {response.status_code} | Content-Type: {response.headers.get('content-type', '')}")

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "image" in content_type:
                return response.content
            else:
                # API returned JSON error instead of image
                print(f"❌ API error response: {response.text[:300]}")
                return None

        elif response.status_code == 503:
            # Model is loading on HF servers — wait and retry
            import time
            wait = int(response.headers.get("X-WaitFor", 20))
            print(f"⏳ Model loading, retrying in {wait}s...")
            time.sleep(wait)

        else:
            print(f"❌ Unexpected status {response.status_code}: {response.text[:300]}")
            return None

    print("❌ All retries exhausted")
    return None


def image_generator_node(state: dict):

    sections = state["plan"]["sections"]
    images = []

    os.makedirs(IMAGES_DIR, exist_ok=True)

    for section in sections[:2]:   # limit to 2 images
        title = section["title"]
        prompt = f"clean minimalist technical illustration explaining: {title}, digital art, professional"

        print(f"\n🎨 Generating image for: {title}")

        image_bytes = query(prompt)

        if image_bytes is None:
            print(f"⚠️ Skipping image for: {title}")
            continue

        # Sanitize filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
        filename = f"{safe_title}.png"
        abs_path = os.path.normpath(os.path.join(IMAGES_DIR, filename))

        with open(abs_path, "wb") as f:
            f.write(image_bytes)

        print(f"✅ Image saved: {abs_path}")

        images.append({
            "section": title,
            "path": abs_path
        })

    return {"images": images}