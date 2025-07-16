import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from seoscan_agent.env import GOOGLE_PSI_API_KEY
from ..utils import normalize_url

def robots_txt_tool(domain: str) -> dict:
    url = urljoin(normalize_url(domain), "/robots.txt")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return {"robots.txt": "Not found"}
        lines = resp.text.strip().splitlines()
        rules = [line for line in lines if line and not line.startswith("#")]
        sitemaps = [line.split(":", 1)[1].strip() for line in rules if line.lower().startswith("sitemap:")]
        return {"robots.txt_url": url, "rules_count": len(rules), "sitemaps": sitemaps, "sample": rules[:5]}
    except Exception as e:
        return {"error": str(e)}

def sitemap_tool(domain: str) -> dict:
    candidates = [
        urljoin(normalize_url(domain), "/sitemap.xml"),
        urljoin(normalize_url(domain), "/sitemap_index.xml"),
    ]
    for url in candidates:
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, "xml")
                urls = [loc.get_text() for loc in soup.find_all("loc")]
                return {"sitemap_url": url, "num_urls": len(urls), "sample_urls": urls[:5]}
        except Exception:
            continue
    return {"sitemap": "Not found"}

def broken_links_tool(domain: str, max_pages: int = 1) -> dict:
    start_url = normalize_url(domain)
    checked = set()
    broken = []
    try:
        resp = requests.get(start_url, timeout=10)
        if resp.status_code != 200:
            return {"error": f"Homepage not reachable ({resp.status_code})"}
        soup = BeautifulSoup(resp.text, "html.parser")
        links = {urljoin(start_url, a["href"]) for a in soup.find_all("a", href=True)}
        links = {l for l in links if urlparse(l).netloc == urlparse(start_url).netloc}
        pages = [start_url] + list(links)[:max_pages]
        for url in pages:
            if url in checked:
                continue
            checked.add(url)
            try:
                r = requests.get(url, timeout=10)
                if r.status_code >= 400:
                    broken.append({"url": url, "status": r.status_code})
            except Exception:
                broken.append({"url": url, "status": "error"})
        return {"broken_links_count": len(broken), "broken_links": broken[:10]}
    except Exception as e:
        return {"error": str(e)}

def http_headers_tool(domain: str) -> dict:
    try:
        r = requests.get(normalize_url(domain), timeout=60)
        return dict(r.headers)
    except Exception as e:
        return {"error": str(e)}

def redirect_check_tool(domain: str) -> dict:
    base = re.sub(r"^https?://", "", domain)
    urls = [
        f"http://{base}", f"https://{base}", f"http://www.{base}", f"https://www.{base}"
    ]
    results = {}
    for u in urls:
        try:
            r = requests.get(u, timeout=60, allow_redirects=True)
            results[u] = {"status": r.status_code, "final_url": r.url}
        except Exception as e:
            results[u] = {"error": str(e)}
    return results

def crawlability_tool(domain: str) -> dict:
    try:
        robots = robots_txt_tool(domain)
        user_agent = "SeoScanBot"
        allow = True
        for rule in robots.get("sample", []):
            if rule.lower().startswith("user-agent") and user_agent.lower() in rule.lower():
                allow = True
            if "disallow: /" in rule.lower():
                allow = False
        homepage = requests.get(normalize_url(domain), timeout=10)
        return {
            "robots_allow_homepage": allow,
            "homepage_status": homepage.status_code,
        }
    except Exception as e:
        return {"error": str(e)}

def lighthouse_tool(domain: str) -> dict:
    import os
    url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    target = normalize_url(domain)
    api_key = GOOGLE_PSI_API_KEY
    try:
        resp = requests.get(
            url,
            params={
                "url": target,
                "key": api_key,
                "strategy": "desktop",
                "category": "performance"
            },
            timeout=30,
        )
        data = resp.json()
        audits = data.get("lighthouseResult", {}).get("audits", {})
        categories = data.get("lighthouseResult", {}).get("categories", {})
        return {
            "performance_score": categories.get("performance", {}).get("score"),
            "first_contentful_paint": audits.get("first-contentful-paint", {}).get("displayValue", ""),
            "speed_index": audits.get("speed-index", {}).get("displayValue", ""),
            "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("displayValue", ""),
            "interactive": audits.get("interactive", {}).get("displayValue", ""),
            "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
            "total_blocking_time": audits.get("total-blocking-time", {}).get("displayValue", ""),
        }
    except Exception as e:
        return {"error": str(e)}