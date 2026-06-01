"""
Lynthz Agent Brain v2.5
Fixed: search routing, per-user memory, indentation bug
"""

import re
import logging
from typing import Optional, AsyncGenerator
from src.memory import MemoryManager
from src.llm_hub import LLMHub
from src.tools.search import SearchTool
from src.tools.weather import WeatherTool
from src.tools.wikipedia import WikipediaTool
from src.tools.maps import GoogleMapsTool
from src.tools.emotion import EmotionDetector
from src.tools.personalization import PersonalizationTool
from src.tools.imagine import ImagineTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lynthz.agent")

SYSTEM_PROMPT = """You are Lynthz, a sharp, intelligent AI assistant. You are fast, precise, and genuinely helpful.

Personality:
- Direct and confident. No fluff, no unnecessary hedging.
- Smart but not robotic — you have personality and emotional awareness.
- You remember context from the conversation.
- You adapt your tone based on how the user is feeling.
- When you search the web, you summarize findings clearly in organized sections.
- For reasoning tasks, you think step-by-step but present cleanly.

CRITICAL RULE — Current Information:
- You have a knowledge cutoff. For ANYTHING about recent events, AI models, software releases,
  news, prices, or anything that could have changed — you MUST search the web first.
- NEVER say "my knowledge cutoff is December 2023" or similar. Instead, search and provide real info.
- If asked about any AI model (Claude, GPT, Gemini, Llama, etc), any tech release, any current event — search first.
- Only answer from memory for timeless facts (math, history before 2023, general concepts).

Response style:
- Use markdown for structure when helpful (headers, bullets, code blocks, tables).
- Keep responses focused. Quality over length.
- Adapt your tone to the user's emotional state.
- Always mention which model you're running on if asked.

{memory_context}
{emotion_context}
{personalization_context}"""

SEARCH_FORCE_KEYWORDS = [
    "latest", "recent", "current", "today", "now", "new", "newest",
    "2024", "2025", "2026", "this year", "this month", "this week",
    "launched", "launch", "released", "release", "announced", "announcement",
    "updated", "update", "version", "upgrade",
    "claude", "gpt", "chatgpt", "openai", "anthropic", "gemini", "llama",
    "deepseek", "mistral", "copilot", "perplexity",
    "model", "llm", "ai model", "benchmark",
    "news", "price", "stock", "score", "result",
    "who won", "what happened", "trending",
    "when did", "when was", "when is", "when will",
    "how much does", "how much is",
    "what's new", "whats new", "bitcoin", "crypto",
    "iphone", "android", "windows", "macos",
]

SEARCH_EXPLICIT_KEYWORDS = [
    "search for", "look up", "search", "google",
    "how to", "tutorial", "guide", "steps to",
]


class Agent:
    def __init__(self, user_id: Optional[str] = None):
        self.memory = MemoryManager(user_id=user_id)
        self.llm = LLMHub()
        self.search = SearchTool()
        self.weather = WeatherTool()
        self.wikipedia = WikipediaTool()
        self.maps = GoogleMapsTool()
        self.emotion = EmotionDetector()
        self.personalization = PersonalizationTool(self.memory)
        self.imagine = ImagineTool()

    def detect_intent(self, message: str) -> dict:
        msg = message.lower().strip()

        # Image Generation
        imagine_keywords = [
            "generate an image", "generate image", "create an image",
            "imagine ", "draw ", "make an image", "make a picture",
            "show me an image", "picture of", "image of", "create a picture"
        ]
        if any(k in msg for k in imagine_keywords):
            prompt = message
            for prefix in ["generate an image of", "generate image of", "create an image of",
                           "imagine ", "draw ", "make an image of", "make a picture of",
                           "show me an image of", "picture of", "image of", "create a picture of"]:
                if msg.startswith(prefix) or f" {prefix}" in msg:
                    idx = msg.find(prefix)
                    prompt = message[idx + len(prefix):].strip()
                    break
            return {"type": "imagine", "prompt": prompt}

        # Personalization
        personalization_patterns = [
            r"my name is", r"call me ",
            r"i(?:'m| am) [a-zA-Z]+",
            r"i (?:love|like|enjoy|am into|am interested in)",
            r"(?:speak|prefer|respond in|language is) [a-zA-Z]+",
            r"timezone is", r"my tz",
            r"(?:casual|formal|professional|relaxed|chill) (?:tone|style|mode|responses?)",
            r"(?:respond|talk|speak) (?:formally|casually|professionally)",
        ]
        if any(re.search(p, msg) for p in personalization_patterns):
            if not any(k in msg for k in ["weather", "search", "find me", "look up",
                                           "launched", "released", "latest", "news",
                                           "price", "current", "today"]):
                return {"type": "personalization", "content": message}

        # Profile query
        if any(k in msg for k in ["my profile", "what do you know about me",
                                   "show my settings", "my preferences"]):
            return {"type": "profile_query"}

        # Weather
        weather_patterns = [r"weather in (.+)", r"weather (?:for|at) (.+)",
                            r"how(?:'s| is) the weather", r"temperature in (.+)"]
        for pattern in weather_patterns:
            match = re.search(pattern, msg)
            if match:
                location = match.group(1) if match.lastindex else "current location"
                return {"type": "weather", "location": location.strip()}

        # STRONG Search — check before Wikipedia/Maps
        if any(k in msg for k in SEARCH_FORCE_KEYWORDS):
            logger.info(f"[INTENT] search (force) — {message[:60]}")
            return {"type": "search", "query": message}

        if any(msg.startswith(k) or f" {k} " in msg for k in SEARCH_EXPLICIT_KEYWORDS):
            logger.info(f"[INTENT] search (explicit) — {message[:60]}")
            return {"type": "search", "query": message}

        # Wikipedia — only for clearly historical/factual
        wiki_keywords = ["who is", "what is", "tell me about", "explain",
                         "history of", "biography of", "definition of", "wikipedia"]
        if any(k in msg for k in wiki_keywords):
            if not any(k in msg for k in ["weather", "restaurant", "near me", "directions",
                                           "launched", "released", "latest", "current", "new",
                                           "price", "today", "2024", "2025", "2026"]):
                return {"type": "wikipedia", "query": message}

        # Maps
        maps_keywords = ["near me", "nearby", "restaurant", "hotel", "directions to",
                         "how to get to", "distance from", "navigate to", "where is the nearest"]
        if any(k in msg for k in maps_keywords):
            location_match = re.search(r"(?:near|in|at|around) (.+?)(?:\?|$)", msg)
            location = location_match.group(1).strip() if location_match else None
            return {"type": "maps", "query": message, "location": location}

        # Memory save
        if any(k in msg for k in ["remember that", "note that", "i prefer", "i work"]):
            return {"type": "memory_save", "content": message}

        logger.info(f"[INTENT] chat — {message[:60]}")
        return {"type": "chat"}

    async def respond(
        self,
        message: str,
        model_key: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:

        if user_id:
            self.memory.set_user_id(user_id)

        intent = self.detect_intent(message)
        logger.info(f"[RESPOND] user={user_id} intent={intent['type']}")

        chosen_model = self.llm.route_model(message, model_key)
        model_info = self.llm.MODELS[chosen_model]

        yield {"type": "model_info", "model": chosen_model,
               "label": model_info["label"], "icon": model_info["icon"]}

        emotion_data = self.emotion.detect(message)
        yield {"type": "emotion_data", "data": self.emotion.format_emotion_display(emotion_data)}

        facts = self.memory.get_facts_summary()
        mem_context = f"\n{facts}" if facts else ""
        emotion_context = self.emotion.get_system_addon(emotion_data)
        personalization_context = self.personalization.get_system_addon()

        system = (SYSTEM_PROMPT
                  .replace("{memory_context}", mem_context)
                  .replace("{emotion_context}", emotion_context)
                  .replace("{personalization_context}", personalization_context))

        full_response = ""

        if intent["type"] == "imagine":
            yield {"type": "searching", "query": f"Generating: {intent['prompt']}"}
            image_data = self.imagine.generate(intent["prompt"])
            yield {"type": "image_data", "data": image_data}
            augmented = (f"{message}\n\n[System: Image generated for '{intent['prompt']}'. "
                         f"Tell user it's ready briefly.]") if "error" not in image_data else (
                         f"{message}\n\n[System: Image failed — {image_data['error']}. Apologize briefly.]")
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "personalization":
            saved = self.personalization.extract_and_save(message)
            name = self.personalization.get_name()
            augmented = (
                f"{message}\n\n[System: Profile updated — {', '.join(saved)}. "
                f"Acknowledge warmly. {'Use their name.' if name else ''}]"
            ) if saved else (
                f"{message}\n\n[System: Personal info received. Respond naturally.]"
            )
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "profile_query":
            summary = self.personalization.get_profile_summary()
            profile_str = (f"Name: {summary['name']}, Style: {summary['response_style']}, "
                           f"Interests: {', '.join(summary['interests']) if summary['interests'] else 'none'}")
            yield {"type": "profile_data", "data": summary}
            augmented = f"{message}\n\n[System: {profile_str}. Present friendly.]"
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "weather":
            weather_data = self.weather.get_weather(intent["location"])
            yield {"type": "weather_data", "data": weather_data}
            if "error" not in weather_data:
                wctx = (f"Weather: {weather_data['description']}, {weather_data['temp']}°C "
                        f"in {weather_data['location']}, {weather_data['country']}. "
                        f"Humidity: {weather_data['humidity']}%. Wind: {weather_data['wind_speed']} m/s.")
                augmented_message = f"{message}\n\n[Weather data: {wctx}]"
            else:
                augmented_message = message
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented_message
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "wikipedia":
            yield {"type": "searching", "query": f"Wikipedia: {message}"}
            wiki_data = self.wikipedia.search(message)
            yield {"type": "wiki_data", "data": wiki_data}
            wiki_context = self.wikipedia.format_for_llm(wiki_data)
            augmented_message = (f"User asked: {message}\n\nWikipedia data:\n{wiki_context}\n\n"
                                 f"Provide a clear, engaging summary.")
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented_message
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "maps":
            yield {"type": "searching", "query": f"Maps: {message}"}
            msg_lower = message.lower()
            if any(k in msg_lower for k in ["directions to", "navigate to", "get to", "distance from"]):
                dest_match = re.search(r"(?:directions to|navigate to|get to) (.+?)(?:\?|$)", msg_lower)
                destination = dest_match.group(1).strip() if dest_match else message
                maps_data = self.maps.get_directions("current location", destination)
            else:
                maps_data = self.maps.search_places(message, intent.get("location"))
            yield {"type": "maps_data", "data": maps_data}
            maps_context = self.maps.format_for_llm(maps_data)
            augmented_message = (f"User asked: {message}\n\nMaps data:\n{maps_context}\n\n"
                                 f"Present this helpfully.")
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented_message
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        elif intent["type"] == "search":
            yield {"type": "searching", "query": message}
            search_data = self.search.search(message)
            yield {"type": "search_results", "data": search_data}
            search_context = self.search.format_for_llm(search_data)
            augmented_message = (
                f"User asked: {message}\n\n"
                f"Web search results (FRESH, just retrieved):\n{search_context}\n\n"
                f"IMPORTANT: Answer using ONLY the search results above. "
                f"Do NOT say you have a knowledge cutoff. "
                f"Do NOT say you cannot access real-time data. "
                f"You just searched the web — use those results to answer directly."
            )
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            history[-1]["content"] = augmented_message
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        else:
            if intent["type"] == "memory_save":
                self.memory.save_fact(message)
            self.memory.add_turn("user", message)
            history = self.memory.get_history()
            async for token in self.llm.stream(history, system, chosen_model):
                full_response += token
                yield {"type": "token", "content": token}

        if full_response:
            self.memory.add_turn("assistant", full_response)

        yield {"type": "done"}

    def get_memory_snapshot(self) -> dict:
        return self.memory.get_memory_snapshot()

    def clear_conversation(self):
        self.memory.clear_short_term()
        self.memory.clear_working()