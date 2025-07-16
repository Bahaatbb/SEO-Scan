import requests
from bs4 import BeautifulSoup
import re
from ..utils import normalize_url

def accessibility_tool(domain: str) -> dict:
    try:
        html = requests.get(normalize_url(domain), timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        imgs = soup.find_all("img")
        no_alt = [img for img in imgs if not img.get("alt")]
        nav = soup.find("nav")
        main = soup.find("main")
        return {
            "img_no_alt": len(no_alt),
            "has_nav": nav is not None,
            "has_main": main is not None,
        }
    except Exception as e:
        return {"error": str(e)}

def mobile_friendly_tool(domain: str) -> dict:
    try:
        html = requests.get(normalize_url(domain), timeout=60).text
        soup = BeautifulSoup(html, "html.parser")
        vp = soup.find("meta", {"name": "viewport"})
        responsive = bool(soup.find("style", string=re.compile("max-width|media")))
        return {
            "viewport_meta": vp.get("content") if vp else "Missing",
            "has_responsive_styles": responsive,
        }
    except Exception as e:
        return {"error": str(e)}