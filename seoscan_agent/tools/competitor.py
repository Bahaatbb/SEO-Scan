import re
import requests
from urllib.parse import urlparse

from seoscan_agent.env import SERPAPI_KEY

from ..utils import normalize_url, serpapi_google_search
from .content import gather_competitor_keywords_tool
from bs4 import BeautifulSoup
from .llm import llm
from llama_index.llms.ollama import Ollama


def extract_search_query(llm, title, desc, keywords):
    context = f"Title: {title}\nDescription: {desc}\nKeywords: {keywords}"
    query_prompt = f"""
You are an expert market analyst.

Given this homepage info:
{context}

Your task:
- Write a short, natural Google search query (4-8 words) that a real user would type to discover brands or organizations offering the same main service/product as this website.
- Do NOT use phrases like 'websites like', 'similar to', 'direct competitors of', 'alternatives to', or the domain name at all.
- Do NOT use quotes, operators, or special symbols.
- Output only the search query, with NO thinking, NO explanations, and NO extra text. Just the query.

Examples:
✓ "hotel booking platforms"
✓ "best travel review websites"
✓ "travel planning services"
✓ "travel advice communities"
✓ "restaurant review platforms"

Now, only output the best search query.
"""
    raw = llm.complete(query_prompt).text.strip()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    query = lines[-1] if lines else ""
    return query


def find_competitors_tool(domain: str, count: int = 5, serpapi_key: str = None) -> list:
    """Find up to 5 real competitor websites for the domain using Google and SerpAPI."""
    html = requests.get(normalize_url(domain), timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"] if meta and meta.get("content") else ""
    combined_keywords = gather_competitor_keywords_tool(domain)["all_competitor_keywords"]

    prompt = f"""
Given these keywords and content for the main site:
    - Title: {title}
    - Description: {desc}
    - Keywords: {combined_keywords}
Create a single, highly-effective Google search query to find this site's direct online competitors (not just similar topics). Output only the query.
"""
    search_query = llm.complete(prompt).text.strip()
    urls = serpapi_google_search(search_query, top_n=count, api_key=SERPAPI_KEY)
    competitors = []
    seen = set()
    for url in urls:
        netloc = urlparse(url).netloc.replace("www.", "")
        dom = netloc.split(":")[0]
        if dom and dom != domain and dom not in seen and domain not in dom:
            competitors.append(dom)
            seen.add(dom)
        if len(competitors) == count:
            break
    return competitors
