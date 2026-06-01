"""
Lynthz Memory System — SaaS version
- Short-term: in-memory conversation turns
- Working: current task context
- Long-term: Supabase memories table per user_id
"""

from datetime import datetime
from typing import Optional

try:
    from src.db import supabase
except Exception:
    supabase = None


class MemoryManager:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.short_term: list[dict] = []
        self.working: dict = {}
        self.MAX_SHORT_TERM = 12

    # ── User ────────────────────────────────────────────────
    def set_user_id(self, user_id: str):
        self.user_id = user_id

    # ── Short-term ──────────────────────────────────────────
    def add_turn(self, role: str, content: str):
        self.short_term.append({
            "role": role,
            "content": content,
            "ts": datetime.now().isoformat()
        })

        if len(self.short_term) > self.MAX_SHORT_TERM:
            self.short_term = self.short_term[-self.MAX_SHORT_TERM:]

    def get_history(self) -> list[dict]:
        return [{"role": t["role"], "content": t["content"]} for t in self.short_term]

    def clear_short_term(self):
        self.short_term = []

    # ── Working memory ──────────────────────────────────────
    def set_working(self, key: str, value):
        self.working[key] = value

    def get_working(self, key: str, default=None):
        return self.working.get(key, default)

    def clear_working(self):
        self.working = {}

    # ── Long-term Supabase memory ───────────────────────────
    def save_fact(self, fact: str):
        if not supabase or not self.user_id or not fact:
            return

        try:
            supabase.table("memories").insert({
                "user_id": self.user_id,
                "memory_text": fact
            }).execute()
        except Exception as e:
            print(f"Memory save error: {e}")

    def set_preference(self, key: str, value: str):
        self.save_fact(f"Preference: {key} = {value}")

    def get_facts_summary(self) -> str:
        if not supabase or not self.user_id:
            return ""

        try:
            result = supabase.table("memories")\
                .select("memory_text, created_at")\
                .eq("user_id", self.user_id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()

            memories = result.data or []

            if not memories:
                return ""

            facts = [m["memory_text"] for m in memories]
            return "Known facts about this user: " + "; ".join(reversed(facts))

        except Exception as e:
            print(f"Memory load error: {e}")
            return ""

    def get_memory_snapshot(self) -> dict:
        facts_count = 0

        if supabase and self.user_id:
            try:
                result = supabase.table("memories")\
                    .select("id", count="exact")\
                    .eq("user_id", self.user_id)\
                    .execute()

                facts_count = result.count or 0
            except Exception:
                pass

        return {
            "user_id": self.user_id,
            "short_term_count": len(self.short_term),
            "working_keys": list(self.working.keys()),
            "facts_count": facts_count,
            "preferences": {}
        }