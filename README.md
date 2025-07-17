# SeoScan Agent

## Abstract

SeoScan Agent is a modular, agentic SEO auditing toolkit that leverages modern LLMs (OpenAI, Ollama, etc.), advanced tool orchestration, and robust web scraping to perform comprehensive, fully-automated SEO audits and competitor benchmarking.
SeoScan is designed for extensibility and transparency, allowing deep technical, content, UX, and competitive SEO analysis for any website.

⸻

Features
• Agentic, modular architecture using LlamaIndex (ReActAgent)
• Multi-agent orchestration (technical, content, UX, competitor)
• Automated web crawling, keyword extraction, Lighthouse/PageSpeed, schema/meta parsing
• Competitor discovery via Google (SerpAPI)
• Support for both OpenAI and Ollama models

⸻

## Setup and Usage

### 1. Clone the Repository

```bash
git clone https://github.com/Bahaatbb/SEO-Scan.git
cd SEO-Scan
```

<hr/>

### 2. Create and Activate a Conda Environment

```bash
conda create -n seoscan python=3.10
conda activate seoscan
```

<hr/>
### 3. Install Dependencies

```bash
# Ensure pip is up to date
python -m pip install --upgrade pip

# Install required libraries
pip install -r requirements.txt
```

### If you need to install a package separately (if any error appears), run:

```bash
pip install llama-index
pip install python-dotenv requests beautifulsoup4
pip install llama-index-llms-ollama
```

<hr/>

### 4. Configure API Keys
### Create a .env

```bash
SERPAPI_KEY=99d84fb70d8436d984662758b9b8b1ec5cabb23869f496d2b395cf2261836522
GOOGLE_PSI_API_KEY=AIzaSyBfvSWi82iBrDM5tOT-5rrnoIwSIXC8NWE
OPENAI_API_KEY=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
```

<hr />

### 5. Install the models
```bash
ollama pull qwen3:4b
```

### Create a .env

```bash
SERPAPI_KEY=99d84fb70d8436d984662758b9b8b1ec5cabb23869f496d2b395cf2261836522
GOOGLE_PSI_API_KEY=AIzaSyBfvSWi82iBrDM5tOT-5rrnoIwSIXC8NWE
OPENAI_API_KEY=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
```

<hr />
### 5. Run the Application
### From the parent directory of your seoscan_agent folder, run:

```bash
python -m seoscan_agent.main
```

<hr/>

### You will see a prompt. Enter SEO queries or domain names as needed, e.g.:

#### examples:

```
SEO audit for aljazeera.com
Do a competitor analysis on wired.com
is ebla-tech.com mobile friendly.
is the robots.txt of tripadvisor.com good
...
...
...
```

## Examples

exmample answers

See ![alt](assets/code.png) for sample queries and usage examples.
See ![alt](assets/code2.png) for sample queries and usage examples.
See ![alt](assets/code3.png) for sample queries and usage examples.
