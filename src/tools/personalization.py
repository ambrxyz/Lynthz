"""
Lynthz Personalization Tool — Supabase Memory Version
"""

import re


class PersonalizationTool:
    def __init__(self, memory_manager):
        self.memory = memory_manager

    def _save_memory(self, text: str):
        if text:
            self.memory.save_fact(text)

    def extract_and_save(self, message: str):
        msg = message.lower().strip()
        response_parts = []

        name_match = re.search(
            r"(?:my name is|call me|i(?:'m| am)) ([a-zA-Z][a-zA-Z\s]{0,30}?)(?:\.|,|$|\s+and)",
            msg
        )
        if name_match:
            name = name_match.group(1).strip().title()
            self._save_memory(f"User name: {name}")
            response_parts.append(f"name: **{name}**")

        tz_match = re.search(
            r"(?:timezone is|my tz is) ([A-Za-z/_\+\-\d\s]{2,30}?)(?:\.|,|$)",
            msg
        )
        if tz_match:
            timezone = tz_match.group(1).strip()
            self._save_memory(f"User timezone: {timezone}")
            response_parts.append(f"timezone: **{timezone}**")

        lang_match = re.search(
            r"(?:speak|prefer|respond in|language is) ([a-zA-Z]{3,20})",
            msg
        )
        if lang_match:
            language = lang_match.group(1).strip().title()
            self._save_memory(f"User language preference: {language}")
            response_parts.append(f"language: **{language}**")

        if any(k in msg for k in ["casual", "informal", "relaxed", "chill"]):
            self._save_memory("User response style preference: casual")
            response_parts.append("style: **casual**")

        elif any(k in msg for k in ["formal", "professional", "serious"]):
            self._save_memory("User response style preference: formal")
            response_parts.append("style: **formal**")

        interest_match = re.search(
            r"(?:i (?:love|like|enjoy|am into|am interested in)) (.+?)(?:\.|,|$)",
            msg
        )
        if interest_match:
            raw = interest_match.group(1).strip()
            interests = [i.strip() for i in re.split(r",| and ", raw) if i.strip()]

            for interest in interests:
                if len(interest) < 40:
                    self._save_memory(f"User interest: {interest}")

            if interests:
                response_parts.append(f"interests: **{', '.join(interests)}**")

        if not response_parts:
            self._save_memory(message)
            response_parts.append("memory saved")

        return response_parts

    def get_name(self):
        facts = self.memory.get_facts_summary()

        match = re.search(r"User name:\s*([^;]+)", facts)
        if match:
            return match.group(1).strip()

        return None

    def get_greeting_name(self):
        name = self.get_name()
        return f", {name}" if name else ""

    def get_response_style(self):
        facts = self.memory.get_facts_summary().lower()

        if "response style preference: casual" in facts:
            return "casual"

        if "response style preference: formal" in facts:
            return "formal"

        return "balanced"

    def get_interests(self):
        facts = self.memory.get_facts_summary()

        interests = re.findall(r"User interest:\s*([^;]+)", facts)
        return [i.strip() for i in interests]

    def get_system_addon(self):
        facts = self.memory.get_facts_summary()
        parts = []

        name = self.get_name()
        if name:
            parts.append(f"The user's name is {name}. Address them by name occasionally.")

        style = self.get_response_style()
        if style == "casual":
            parts.append("Use a relaxed, friendly, conversational tone.")
        elif style == "formal":
            parts.append("Use a professional, formal tone. Avoid slang.")

        interests = self.get_interests()
        if interests:
            top = ", ".join(interests[:5])
            parts.append(f"User interests include: {top}. Reference these when relevant.")

        if facts:
            parts.append(f"Long-term memory: {facts}")

        if not parts:
            return ""

        return "\n\nUser profile:\n" + "\n".join(f"- {pt}" for pt in parts)

    def get_profile_summary(self):
        return {
            "name": self.get_name() or "Not set",
            "timezone": "Stored in memory if provided",
            "language": "Stored in memory if provided",
            "response_style": self.get_response_style(),
            "interests": self.get_interests(),
            "updated": ""
        }