import os
import re
import logging
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

logger = logging.getLogger(__name__)

HF_API_KEY = os.getenv("HF_API_KEY")

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "generated_images"))

# InferenceClient with provider="auto" automatically picks the best
# available provider for the model — no more manual URL management.
client = InferenceClient(
    provider="auto",
    api_key=HF_API_KEY,
)


def _generate_image(prompt: str) -> bytes | None:
    """
    Uses HuggingFace InferenceClient to generate an image from a text prompt.
    FLUX.1-schnell is the free, fast model — works reliably on the free tier.
    Returns raw PNG bytes, or None if generation fails.
    """
    try:
        # Returns a PIL Image object directly
        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell",
        )

        # Convert PIL Image to raw bytes for saving to disk
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return None


def image_generator_node(state: dict) -> dict:
    """
    Generates one illustration per blog section (capped at 2).
    Images are saved locally and referenced by relative path
    so they work both locally and on Azure.
    """
    sections = state["plan"]["sections"]
    images   = []

    os.makedirs(IMAGES_DIR, exist_ok=True)

    for section in sections[:2]:
        title  = section["title"]
        prompt = (
            f"clean minimalist technical illustration explaining: {title}, "
            "digital art, professional, white background"
        )

        logger.info(f"Generating image for section: '{title}'")

        image_bytes = _generate_image(prompt)

        if image_bytes is None:
            logger.warning(f"Skipping image for section: '{title}'")
            continue

        safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
        filename   = f"{safe_title}.png"
        rel_path   = os.path.join("generated_images", filename)
        abs_path   = os.path.join(IMAGES_DIR, filename)

        with open(abs_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"Image saved: {rel_path}")

        images.append({
            "section": title,
            "alt":     title,
            "path":    rel_path
        })

    return {"images": images}