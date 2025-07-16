import requests
from urllib.parse import urlparse

from .env import SERPAPI_KEY


def normalize_url(domain: str) -> str:
    if not domain.startswith(("http://", "https://")):
        return "https://" + domain.lstrip("/")
    return domain


def serpapi_google_search(query, top_n=5, api_key=None):
    """Search Google using SerpAPI and return up to top_n unique result URLs."""

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": top_n
    }
    url = "https://serpapi.com/search.json"
    r = requests.get(url, params=params, timeout=20)
    results = r.json()
    urls = []
    seen = set()
    for res in results.get("organic_results", []):
        link = res.get("link")
        netloc = urlparse(link).netloc.replace("www.", "") if link else ""
        if not link or not netloc or netloc in seen:
            continue
        urls.append(link)
        seen.add(netloc)
        if len(urls) == top_n:
            break
    return urls
