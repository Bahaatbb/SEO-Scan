from llama_index.core.tools import FunctionTool
from llama_index.core.agent.react import ReActAgent
from llama_index.llms.openai import OpenAI

from .env import SERPAPI_KEY, OPENAI_API_KEY
from .prompts import (
    SYSTEM_PROMPT, TECHNICAL_PROMPT, CONTENT_PROMPT, UX_PROMPT
)
from .tools.technical import *
from .tools.content import *
from .tools.ux import *
from .tools.competitor import *

llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.3, request_timeout=990)



def smart_competitor_analysis(domain: str, serpapi_key: str):
    """Full competitor SEO audit: discover real competitors, audit each, compare all, synthesize a detailed report in markdown."""
    print(f"\n[INFO] [smart_competitor_analysis] Getting homepage details for {domain} ...")
    html = requests.get(normalize_url(domain), timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"] if meta and meta.get("content") else ""
    words = re.findall(r'\b\w{4,}\b', (title + " " + desc).lower())
    combined_keywords = list(dict.fromkeys(words))[:6]
    print(f"[DEBUG] Homepage title: {title}")
    print(f"[DEBUG] Homepage desc: {desc}")
    print(f"[DEBUG] Combined keywords: {combined_keywords}")

    llm = Ollama(model="qwen3:4b", request_timeout=120)
    search_query = extract_search_query(llm, title, desc, combined_keywords)
    print(f"[DEBUG] Final Search Query: {search_query}")

    urls = serpapi_google_search(search_query, top_n=8, api_key=SERPAPI_KEY)
    main_domain = urlparse(normalize_url(domain)).netloc.replace("www.", "")
    EXCLUDED_DOMAINS = [
        "wikipedia", "github", "reddit", "stack", "quora", "news.ycombinator", "google", "pdf",
        "docs.", "blog.", "wordpress", "medium.", ".gov", ".edu", "pinterest", "linkedin", "twitter", "facebook"
    ]
    competitors = []
    seen = set()
    for url in urls:
        netloc = urlparse(url).netloc.replace("www.", "")
        if (
            not netloc
            or netloc == main_domain
            or netloc in seen
            or main_domain in netloc
            or netloc in main_domain
            or any(ex in netloc for ex in EXCLUDED_DOMAINS)
        ):
            continue
        competitors.append(netloc)
        seen.add(netloc)
        if len(competitors) == 5:
            break

    print(f"[INFO] Discovered competitors: {competitors}")

    # Audit main + competitors using agents
    all_domains = [main_domain] + competitors
    audits = {}
    keyword_focuses = {}
    for d in all_domains:
        print(f"[INFO] Auditing {d} ...")
        audits[d] = {
            "technical": TechnicalAgent.chat(f"Audit technical SEO for {d}"),
            "content": ContentAgent.chat(f"Audit content SEO for {d}"),
            "ux": UXAgent.chat(f"Audit UX and mobile SEO for {d}"),
        }
        keyword_focuses[d] = ContentAgent.chat(
            f"Run keyword_extraction_tool on {d} and summarize the top keywords with brief explanations."
        )
        print(f"[DEBUG] Audit for {d} complete.")

    # Construct report prompt for LLM agent
    import json
    final_report_prompt = f"""
You are SeoScan, a senior SEO consultant.
Here are detailed audit results for the MAIN WEBSITE and its competitors.

MAIN WEBSITE: {main_domain}
COMPETITORS: {', '.join(competitors)}

## Technical, Content, and UX Audits (JSON):
{json.dumps(audits, indent=2)}

## Keyword Focus Analyses (JSON):
{json.dumps(keyword_focuses, indent=2)}

Instructions:
- Output MUST be long, thorough, with each tool fully explained and never skipped. Use markdown (sections, tables, bullets). Minimum 700 words. If findings are brief, expand with best practices.
synthesize a big, comprehensive, sectioned answer after running all relevant tools, it will try to be efficient, not exhaustive.
- Write a LONG, professional, markdown-formatted competitor audit report, at least 1500 words.
- Start with an executive summary (at least 400 words) on how the main website compares to competitors.
- For each SEO aspect (robots.txt, sitemap, performance, schema, accessibility, mobile, headers, redirects, keyword focus), explain what it is and why it matters for SEO.
- In a comparison table, summarize each site's strengths and weaknesses for all SEO topics.
- Write bullet-point lists of strengths/weaknesses for each site.
- Add a full "Keyword Focus Analysis" section for each domain, showing and commenting on its main keywords.
- End with an "Actionable Recommendations" section for the main website, referencing what competitors do better and a prioritized to-do list.
- The report MUST be DETAILED, COMPREHENSIVE, LONG, and USE RICH MARKDOWN with headings, tables, and lists.
- DO NOT output summaries or short answers. Expand with best practices and further observations if short.
- NEVER output placeholder competitor names—use only real discovered domains.

---
"""
    print("[DEBUG] Submitting audits and keyword focus data to LLM for report synthesis...")
    report = llm.complete(final_report_prompt).text
    print("[DEBUG] Report synthesis complete.\n")
    return report

def competitor_agent_tool(domain: str) -> str:
    """
    Discover real competitors, audit all (main+competitors), synthesize a full-length markdown SEO report.
    Includes detailed debugging checkpoints for every critical step.
    """
    import json


    # 1. Fetch homepage and extract info
    try:
        html = requests.get(normalize_url(domain), timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta = soup.find("meta", attrs={"name": "description"})
        desc = meta["content"] if meta and meta.get("content") else ""
        kw_result = keyword_extraction_tool(domain)
        keywords = kw_result.get("top_keywords", [])
    except Exception as e:
        return f"Error fetching homepage info for {domain}: {e}"

    # 2. Ask LLM for a realistic Google query
    try:
        prompt = f"""
You are an SEO and market analysis expert.
Given this site's info:
Title: {title}
Description: {desc}
Keywords: {keywords}

Write a short, natural Google search query (4-8 words) that a real user would type to discover brands or organizations offering the same main service or product as this website.
- Do NOT use phrases like 'websites like', 'alternatives to', 'direct competitors of', or the domain name at all.
- Do NOT use quotes, operators, or special symbols.
- Output only the search query, with NO thinking, NO explanations, and NO extra text. Just the query.
"""
        search_query = llm.complete(prompt).text.strip().splitlines()[-1]
    except Exception as e:
        return f"Error generating competitor discovery query: {e}"

    # 3. Use SerpAPI to get competitor URLs
    try:
        competitor_urls = serpapi_google_search(search_query, top_n=8, api_key=SERPAPI_KEY)
    except Exception as e:
        return f"Error in competitor search: {e}"

    # 4. Filter competitors
    EXCLUDED = [
        "wikipedia", "github", "reddit", "stack", "quora", "news.ycombinator", "google", "pdf",
        "docs.", "blog.", "wordpress", "medium.", ".gov", ".edu", "pinterest", "linkedin", "twitter", "facebook"
    ]
    main_netloc = urlparse(normalize_url(domain)).netloc.replace("www.", "")
    competitors = []
    seen = set()
    for url in competitor_urls:
        netloc = urlparse(url).netloc.replace("www.", "")
        if (
            not netloc or netloc == main_netloc or netloc in seen or
            main_netloc in netloc or netloc in main_netloc or
            any(ex in netloc for ex in EXCLUDED)
        ):
            continue
        competitors.append(netloc)
        seen.add(netloc)
        if len(competitors) >= 4:
            break

    # 5. Audit each domain
    audits = {}
    for d in [main_netloc] + competitors:
        try:
            audits[d] = {
                "technical": technical_agent_tool(d),
                "content": content_agent_tool(d),
                "ux": ux_agent_tool(d),
            }
            # Prepare readable summary for debug and LLM prompt
            summary = {}
            for k, v in audits[d].items():
                if hasattr(v, "response"):
                    summary[k] = v.response
                elif hasattr(v, "text"):
                    summary[k] = v.text
                else:
                    summary[k] = str(v)
            debug_str = json.dumps(summary, indent=2)[:1500]

            # Save summary for LLM
            audits[d] = summary
        except Exception as e:
            audits[d] = {"error": str(e)}
    # 6. LLM synthesis prompt for full-length markdown report
    synth_prompt = f"""
You are SeoScan, a senior SEO consultant.

MAIN WEBSITE: {main_netloc}
COMPETITORS: {', '.join(competitors)}

Here are technical, content, and UX audits for each (in JSON):

{json.dumps(audits, indent=2)}

Instructions:
- Write a LONG, professional, markdown-formatted competitor audit report, at LEAST 1500 words.
- Start with an executive summary (at LEAST 400 words) comparing the main site to its real competitors.
- For each SEO aspect (robots.txt, sitemap, performance, schema, accessibility, mobile, headers, redirects, keyword focus), explain what it is, why it matters, and compare findings.
- Add a comparison table, strengths/weaknesses, and keyword focus analysis for every site.
- Finish with prioritized actionable recommendations for the main website, referencing what competitors do better.
- Never use placeholder names. Always use the actual discovered competitor domains.
- Expand with best practices and further observations if any section is brief.
"""

    print("[DEBUG] Sending all audits to LLM for synthesis of final report...")
    try:
        result = llm.complete(synth_prompt)
        final_report = result.text if hasattr(result, "text") else str(result)
    except Exception as e:
        return f"Error generating final competitor report: {e}"

    return final_report

TECHNICAL_TOOLS = [
    FunctionTool.from_defaults(fn=robots_txt_tool, name="robots_txt_tool", description=robots_txt_tool.__doc__),
    FunctionTool.from_defaults(fn=sitemap_tool, name="sitemap_tool", description=sitemap_tool.__doc__),
    FunctionTool.from_defaults(fn=broken_links_tool, name="broken_links_tool", description=broken_links_tool.__doc__),
    FunctionTool.from_defaults(fn=http_headers_tool, name="http_headers_tool", description=http_headers_tool.__doc__),
    FunctionTool.from_defaults(fn=redirect_check_tool, name="redirect_check_tool", description=redirect_check_tool.__doc__),
    FunctionTool.from_defaults(fn=lighthouse_tool, name="lighthouse_tool", description=lighthouse_tool.__doc__),
    FunctionTool.from_defaults(fn=crawlability_tool, name="crawlability_tool", description=crawlability_tool.__doc__),
]

CONTENT_TOOLS = [
    FunctionTool.from_defaults(fn=schema_validation_tool, name="schema_validation_tool", description=schema_validation_tool.__doc__),
    FunctionTool.from_defaults(fn=keyword_extraction_tool, name="keyword_extraction_tool", description=keyword_extraction_tool.__doc__),
    FunctionTool.from_defaults(fn=llm_keywords_from_content_tool, name="llm_keywords_from_content_tool", description=llm_keywords_from_content_tool.__doc__),
    FunctionTool.from_defaults(fn=gather_competitor_keywords_tool, name="gather_competitor_keywords_tool", description=gather_competitor_keywords_tool.__doc__),
]

UX_TOOLS = [
    FunctionTool.from_defaults(fn=accessibility_tool, name="accessibility_tool", description=accessibility_tool.__doc__),
    FunctionTool.from_defaults(fn=mobile_friendly_tool, name="mobile_friendly_tool", description=mobile_friendly_tool.__doc__),
]

COMPETITOR_TOOLS = [
    FunctionTool.from_defaults(
        fn=lambda domain, count=5: find_competitors_tool(domain, count, serpapi_key=SERPAPI_KEY),
        name="find_competitors_tool",
        description="Finds up to 5 real competitor websites for the domain using Google and SerpAPI"
    ),
     FunctionTool.from_defaults(
         fn=lambda domain: smart_competitor_analysis(domain, serpapi_key=SERPAPI_KEY),
         name="smart_competitor_analysis",
         description="Performs full competitor audit using SerpAPI/Google competitor discovery"
     ),
]


TechnicalAgent = ReActAgent.from_tools(TECHNICAL_TOOLS, max_iterations=40, llm=llm, system_prompt=TECHNICAL_PROMPT)
ContentAgent = ReActAgent.from_tools(CONTENT_TOOLS, max_iterations=40, llm=llm, system_prompt=CONTENT_PROMPT)
UXAgent = ReActAgent.from_tools(UX_TOOLS, llm=llm, max_iterations=40, system_prompt=UX_PROMPT)


def technical_agent_tool(domain: str) -> str:
    return TechnicalAgent.chat(f"Run each technical SEO tool ONCE on {domain}. Do not call other agents or tools recursively.")

def content_agent_tool(domain: str) -> str:
    return ContentAgent.chat(f"SEO audit for {domain}")

def ux_agent_tool(domain: str) -> str:
    return UXAgent.chat(f"SEO audit for {domain}")

SUBAGENT_TOOLS = [
    FunctionTool.from_defaults(fn=technical_agent_tool, name="technical_agent_tool", description="Calls the TechnicalAgent subagent."),
    FunctionTool.from_defaults(fn=content_agent_tool, name="content_agent_tool", description="Calls the ContentAgent subagent."),
    FunctionTool.from_defaults(fn=ux_agent_tool, name="ux_agent_tool", description="Calls the UXAgent subagent."),
    FunctionTool.from_defaults(fn=competitor_agent_tool, name="competitor_agent_tool", description="Calls the CompetitorAgent for competitor analysis subagent."),
]

ALL_TOOLS = TECHNICAL_TOOLS + CONTENT_TOOLS + UX_TOOLS + SUBAGENT_TOOLS

SeoOrchestrator = ReActAgent.from_tools(
    ALL_TOOLS, llm=llm, max_iterations=120, system_prompt=SYSTEM_PROMPT,
)
