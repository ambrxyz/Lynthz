"""
Lynthz Image Generation — Pollinations.ai
Free, no API key, FLUX model quality
"""

import requests
import urllib.parse


class ImagineTool:
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"

    def generate(self, prompt: str) -> dict:
        try:
            # Enhance prompt for better quality
            enhanced = f"{prompt}, high quality, detailed, sharp"
            encoded = urllib.parse.quote(enhanced)
            image_url = f"{self.base_url}/{encoded}?width=768&height=768&nologo=true"

            # Verify the URL actually returns an image
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200:
                return {
                    "success": True,
                    "image_url": image_url,
                    "prompt": prompt
                }
            else:
                return {"error": f"Failed to generate image: {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def format_for_llm(self, data: dict) -> str:
        if "error" in data:
            return f"Image generation failed: {data['error']}"
        return f"Image generated successfully for prompt: {data['prompt']}"