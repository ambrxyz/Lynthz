"""
Lynthz LLM Hub — Multi-model router
"""

import os
from typing import AsyncGenerator, Optional
from groq import Groq


class LLMHub:
    MODELS = {
        "llama": {
            "id": "llama-3.3-70b-versatile",
            "provider": "groq",
            "label": "Llama 3.3 70B",
            "description": "Fast, great for chat & general tasks",
            "icon": "⚡"
        },
        "deepseek": {
            "id": "deepseek-r1-distill-llama-70b",
            "provider": "groq",
            "label": "DeepSeek R1",
            "description": "Deep reasoning, complex problems",
            "icon": "🧠"
        },
        "gemini": {
            "id": "gemini-2.0-flash",
            "provider": "gemini",
            "label": "Gemini 2.0 Flash",
            "description": "Search-augmented, long context",
            "icon": "✦"
        },
        "mixtral": {
            "id": "llama-3.1-8b-instant",
            "provider": "groq",
            "label": "Mixtral 8x7B",
            "description": "Balanced, multilingual",
            "icon": "◈"
        }
    }

    # Fallback chain — if a model fails, try the next one
    FALLBACK_CHAIN = ["llama", "mixtral"]

    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Make sure your .env file is in the "
                "lynthz/ folder with: GROQ_API_KEY=your_key_here"
            )
        self.groq = Groq(api_key=groq_key)
        self._gemini_key = os.getenv("GEMINI_API_KEY")

    def route_model(self, message: str, user_model: Optional[str] = None) -> str:
        if user_model and user_model in self.MODELS:
            return user_model
        msg = message.lower()
        reasoning = ["explain why", "analyze", "compare", "pros and cons", "should i",
                     "logic", "reason", "step by step", "solve", "math", "calculate",
                     "write the", "code", "c++", "python", "javascript", "algorithm"]
        if any(k in msg for k in reasoning):
            return "deepseek"
        search = ["search", "latest", "news", "current", "today", "2025", "2026",
                  "what happened", "recent", "find", "look up", "weather", "who is"]
        if any(k in msg for k in search):
            return "gemini" if self._gemini_key else "llama"
        return "llama"

    async def stream(self, messages: list, system_prompt: str, model_key: str = "llama") -> AsyncGenerator[str, None]:
        model = self.MODELS.get(model_key, self.MODELS["llama"])
        if model["provider"] == "groq":
            async for t in self._groq_stream_with_fallback(messages, system_prompt, model_key):
                yield t
        elif model["provider"] == "gemini":
            async for t in self._gemini_stream(messages, system_prompt):
                yield t

    async def _groq_stream_with_fallback(self, messages: list, system_prompt: str, model_key: str) -> AsyncGenerator[str, None]:
        # Try requested model first, then fallback chain
        keys_to_try = [model_key] + [k for k in self.FALLBACK_CHAIN if k != model_key]
        for key in keys_to_try:
            model_id = self.MODELS[key]["id"]
            try:
                async for t in self._groq_stream(messages, system_prompt, model_id):
                    yield t
                return  # success — stop
            except Exception as e:
                err = str(e).lower()
                # Silently fallback on rate limits, quota, or invalid model errors
                if any(x in err for x in ["decommissioned", "not found", "invalid", "429", "rate", "limit", "quota", "exhausted", "token"]):
                    continue  # silently try next model
                else:
                    yield f"\n\n⚠️ Model error: {str(e)}"
                    return
        yield "\n\n⚠️ All models unavailable right now. Please try again in a few minutes."

    async def _groq_stream(self, messages: list, system_prompt: str, model_id: str) -> AsyncGenerator[str, None]:
        full = [{"role": "system", "content": system_prompt}] + messages
        stream = self.groq.chat.completions.create(
            model=model_id, messages=full, stream=True,
            max_tokens=2048, temperature=0.7,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def _gemini_stream(self, messages: list, system_prompt: str) -> AsyncGenerator[str, None]:
        if not self._gemini_key:
            async for t in self._groq_stream(messages, system_prompt, "llama-3.3-70b-versatile"):
                yield t
            return
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self._gemini_key)
            contents = []
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=2048,
                temperature=0.7,
            )
            response = client.models.generate_content_stream(
                model="gemini-2.0-flash", contents=contents, config=config
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            err = str(e).lower()
            # Quota/rate limit — silently fallback to Llama 3.1 8B
            if "429" in str(e) or "quota" in err or "exhausted" in err or "rate" in err:
                async for t in self._groq_stream(messages, system_prompt, "llama-3.1-8b-instant"):
                    yield t
            else:
                async for t in self._groq_stream(messages, system_prompt, "llama-3.1-8b-instant"):
                    yield t

    def get_models_info(self) -> list:
        return [{"key": k, **v} for k, v in self.MODELS.items()]