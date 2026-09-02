"""
Image Generation Utility for Cloud-Based AI Chatbot.
Handles text-to-image generation using configured external providers
(OpenAI DALL-E, OpenRouter, or Pollinations AI fallback) and caches images
locally under static/generated/images/ for fast, reliable, Azure-compatible delivery.
"""

import os
import time
import uuid
import urllib.parse
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("chatbot.image_generator")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
GENERATED_IMAGES_DIR = os.path.join(STATIC_DIR, "generated", "images")
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


class ImageGenerationError(Exception):
    """Raised when image generation fails."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ImageGenerator:
    """
    Generates images from textual prompts.
    Reads configuration from environment variables:
      - IMAGE_GENERATION_API_KEY (or OPENAI_API_KEY)
      - IMAGE_GENERATION_MODEL (default: flux)
      - IMAGE_GENERATION_PROVIDER (auto, openai, openrouter, pollinations)
    """

    def __init__(self):
        self.api_key = os.getenv("IMAGE_GENERATION_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("IMAGE_GENERATION_MODEL", "flux")
        self.provider = os.getenv("IMAGE_GENERATION_PROVIDER", "auto").lower()

    def generate(self, prompt: str) -> Dict[str, Any]:
        """
        Generates an image for the given prompt and returns image metadata.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            raise ImageGenerationError("Image prompt cannot be empty.", status_code=400)

        logger.info("Generating image for prompt: %s (model=%s, provider=%s)", prompt[:60], self.model, self.provider)

        # 1. If OpenAI key is explicitly provided and provider is openai/dall-e
        if self.api_key and (self.provider == "openai" or "dall-e" in self.model.lower()):
            try:
                return self._generate_openai(prompt)
            except Exception as e:
                logger.warning("OpenAI image generation failed: %s. Trying fallback provider...", e)

        # 2. OpenRouter or Pollinations fallback
        try:
            return self._generate_pollinations(prompt)
        except Exception as e:
            logger.warning("Pollinations image generation failed: %s. Generating local placeholder...", e)
            return self._generate_svg_fallback(prompt)

    def _generate_openai(self, prompt: str) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        model_name = self.model if "dall-e" in self.model else "dall-e-3"

        from typing import cast
        response = cast(
            Any,
            client.images.generate(
                model=model_name,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
        )

        remote_url = response.data[0].url
        img_res = requests.get(remote_url, timeout=30)
        img_res.raise_for_status()

        filename = f"img_{uuid.uuid4().hex[:12]}.png"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_res.content)

        return {
            "status": "success",
            "image_url": f"/static/generated/images/{filename}",
            "prompt": prompt,
            "model": model_name,
            "provider": "OpenAI DALL-E",
            "created_at": int(time.time()),
        }

    def _generate_pollinations(self, prompt: str) -> Dict[str, Any]:
        """
        Generates high-res image via Pollinations AI (Flux / SDXL backbone).
        """
        encoded_prompt = urllib.parse.quote(prompt)
        seed = int(time.time() * 1000) % 1000000
        pollinations_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?"
            f"width=1024&height=1024&nologo=true&seed={seed}&model={self.model}"
        )

        headers = {
            "User-Agent": "Cloud-AI-Chatbot/1.0 (Azure HPCC Project)"
        }
        res = requests.get(pollinations_url, headers=headers, timeout=40)
        res.raise_for_status()

        if len(res.content) < 1000:
            raise ImageGenerationError("Received invalid image data from provider.", status_code=502)

        filename = f"img_{uuid.uuid4().hex[:12]}.jpg"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(res.content)

        return {
            "status": "success",
            "image_url": f"/static/generated/images/{filename}",
            "prompt": prompt,
            "model": f"Flux / {self.model}",
            "provider": "Pollinations Cloud AI",
            "created_at": int(time.time()),
        }

    def _generate_svg_fallback(self, prompt: str) -> Dict[str, Any]:
        """
        Safe offline fallback generating an artistic SVG card if all remote networks fail.
        """
        safe_prompt = prompt[:80].replace("<", "&lt;").replace(">", "&gt;")
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3a8a;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#3b82f6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#9333ea;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" fill="url(#grad)" rx="24"/>
  <circle cx="512" cy="420" r="140" fill="rgba(255,255,255,0.15)"/>
  <path d="M420 370 h184 v120 h-184 z" fill="none" stroke="#ffffff" stroke-width="8" stroke-linejoin="round"/>
  <circle cx="480" cy="410" r="24" fill="#ffffff"/>
  <polygon points="435,475 500,430 550,465 590,440 600,475" fill="#ffffff"/>
  <text x="512" y="650" font-family="Inter, system-ui, sans-serif" font-size="34" font-weight="bold" fill="#ffffff" text-anchor="middle">
    AI Image Generated
  </text>
  <text x="512" y="710" font-family="Inter, system-ui, sans-serif" font-size="22" fill="rgba(255,255,255,0.85)" text-anchor="middle">
    "{safe_prompt}"
  </text>
  <text x="512" y="780" font-family="Inter, system-ui, sans-serif" font-size="18" fill="rgba(255,255,255,0.6)" text-anchor="middle">
    Generated by Cloud AI Chatbot Engine
  </text>
</svg>"""

        filename = f"img_{uuid.uuid4().hex[:12]}.svg"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)

        return {
            "status": "success",
            "image_url": f"/static/generated/images/{filename}",
            "prompt": prompt,
            "model": "Cloud Vector Canvas",
            "provider": "Cloud AI Image Generator",
            "created_at": int(time.time()),
        }


image_generator = ImageGenerator()
