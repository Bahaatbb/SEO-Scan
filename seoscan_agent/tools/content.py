import re

import requests
from bs4 import BeautifulSoup
from llama_index.llms.openai import OpenAI

from seoscan_agent.env import OPENAI_API_KEY

from ..utils import normalize_url


def keyword_extraction_tool(domain: str, max_keywords: int = 10) -> dict:
    """Extract top keywords from homepage content."""
    try:
        html = requests.get(normalize_url(domain), timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=' ', strip=True).lower()
        words = re.findall(r'\b\w{4,}\b', text)
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        return {"top_keywords": [k for k, _ in sorted_keywords]}
    except Exception as e:
        return {"top_keywords": [], "error": str(e)}

def schema_validation_tool(domain: str) -> dict:
    try:
        html = requests.get(normalize_url(domain), timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        schemas = soup.find_all("script", {"type": re.compile("ld\\+json")})
        og = soup.find_all("meta", {"property": re.compile("^og:")})
        twitter = soup.find_all("meta", {"name": re.compile("^twitter:")})
        return {
            "jsonld_blocks": len(schemas),
            "og_tags": [m.get("property") for m in og],
            "twitter_tags": [m.get("name") for m in twitter],
            "sample_schema": [s.get_text()[:200] for s in schemas[:1]]
        }
    except Exception as e:
        return {"error": str(e)}

def llm_keywords_from_content_tool(html: str) -> dict:
    llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.3, request_timeout=990)
    prompt = f"""
You are an expert at identifying a website's main topics for SEO/competitor analysis.
Given this homepage HTML/text:

{html[:2000]}

List 3 and only 3 highly relevant SEO keywords (single words or short phrases, comma-separated) that best capture what this site is about.
ONLY output the keywords, comma-separated, with NO extra text.
"""
    resp = llm.complete(prompt)
    if hasattr(resp, 'text'):
        result = resp.text
    else:
        result = str(resp)
    keywords = [k.strip() for k in result.split(",") if k.strip()]
    return {"llm_keywords": keywords}

def gather_competitor_keywords_tool(domain: str) -> dict:
    html = requests.get(normalize_url(domain), timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"] if meta and meta.get("content") else ""
    basic_keywords = re.findall(r'\b\w{4,}\b', (title + " " + desc).lower())
    unique_basic = list(dict.fromkeys(basic_keywords))[:5]
    llm_result = llm_keywords_from_content_tool(html)
    all_keywords = list(dict.fromkeys(unique_basic + llm_result.get("llm_keywords", [])))
    return {"all_competitor_keywords": all_keywords}