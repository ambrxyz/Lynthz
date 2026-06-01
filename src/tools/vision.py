"""Lynthz Vision Tool — image/file analysis via Groq"""

import os
import base64
from groq import Groq


class VisionTool:
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def analyze_image(self, image_base64: str, mime_type: str, prompt: str) -> str:
        response = self.groq.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or "Analyze this image in detail."
                    }
                ]
            }],
            max_tokens=1024,
        )
        return response.choices[0].message.content