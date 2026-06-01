import requests

class WikipediaTool:
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"

    def search(self, query, sentences=5):
        try:
            params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 3}
            resp = requests.get(self.SEARCH_URL, params=params, timeout=10)
            results = resp.json().get("query", {}).get("search", [])
            if not results:
                return {"error": "No results found"}
            summary = self._get_summary(results[0]["title"])
            summary["related"] = [r["title"] for r in results[1:3]]
            return summary
        except Exception as e:
            return {"error": str(e)}

    def _get_summary(self, title):
        try:
            url = f"{self.BASE_URL}/page/summary/{requests.utils.quote(title)}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return {"title": data.get("title", title), "summary": data.get("extract", ""), "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""), "type": "wikipedia"}
        except Exception as e:
            return {"error": str(e)}

    def format_for_llm(self, data):
        if "error" in data:
            return f"Wikipedia error: {data['error']}"
        return f"Wikipedia - {data['title']}:\n{data['summary']}"