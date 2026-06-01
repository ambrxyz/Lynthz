"""
Lynthz Search Tool — Tavily + structured result cards
Results are parsed and summarized, never raw JSON dumps.
"""

import os
import requests
from typing import Optional


class SearchTool:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> dict:
        """
        Returns structured search results ready for display as cards.
        """
        if not self.api_key:
            return {"error": "No Tavily API key configured", "results": []}

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            }
            resp = requests.post(self.base_url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Structure results into clean cards
            cards = []
            for r in data.get("results", []):
                cards.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:280],
                    "score": round(r.get("score", 0), 2),
                    "published": r.get("published_date", "")
                })

            return {
                "query": query,
                "answer": data.get("answer", ""),   # Tavily's quick answer
                "cards": cards,
                "count": len(cards)
            }

        except requests.exceptions.Timeout:
            return {"error": "Search timed out", "results": []}
        except Exception as e:
            return {"error": str(e), "results": []}

    def format_for_llm(self, search_data: dict) -> str:
        """Format search results as context for the LLM to summarize."""
        if "error" in search_data:
            return f"Search failed: {search_data['error']}"

        lines = [f"Search query: {search_data['query']}"]

        if search_data.get("answer"):
            lines.append(f"Quick answer: {search_data['answer']}")

        lines.append(f"\nTop {search_data['count']} results:")
        for i, card in enumerate(search_data["cards"], 1):
            lines.append(f"\n[{i}] {card['title']}")
            lines.append(f"    URL: {card['url']}")
            lines.append(f"    {card['snippet']}")

        return "\n".join(lines)
