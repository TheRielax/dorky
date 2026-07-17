# DORKY 🕵️‍♂️
### Advanced Multi-Engine Dorking & Dynamic Syntax Adapter
**Author**: [rielax](https://github.com/TheRielax)

```text
              ██████╗  ██████╗ ██████╗ ██╗  ██╗██╗   ██╗
              ██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝╚██╗ ██╔╝
              ██║  ██║██║   ██║██████╔╝█████╔╝  ╚████╔╝ 
              ██║  ██║██║   ██║██╔══██╗██╔═██╗   ╚██╔╝  
              ██████╔╝╚██████╔╝██║  ██║██║  ██╗   ██║   
              ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
```

**DORKY** is a powerful, Python-based reconnaissance tool designed to dynamically build, adapt, and execute advanced search queries across multiple major search engines (**DuckDuckGo**, **Bing**, **Google**, **Brave Search**, and **Yandex**).

Unlike traditional dorking scripts that assume standard Google syntax works everywhere, **DORKY features an intelligent Dynamic Syntax Adapter** that converts canonical search queries into the exact, native syntax supported by each individual engine.

---

## ✨ Key Features

- **🔄 Multi-Engine Dynamic Adaptation**: Automatically translates canonical search operators (`filetype:`, `intitle:`, `inurl:`, `intext:`, `-exclude`, exact quotes) into engine-specific equivalents (e.g., Yandex `mime:`, `title:`, `url:`; Bing `inbody:`).
- **🕵️‍♂️ Target Recon & OSINT Suite (Ashok Inspired)**:
  - **🏗️ Target Infrastructure, Domain & Web Footprinting Suite**: Consolidated reconnaissance suite merging passive subdomain discovery, structural site tree fingerprinting, and DNS/security audits into a single command center featuring 4 specialized modes:
    - **🌐 Passive DNS, WHOIS & Security Posture (SPF/DMARC Auditor)**: Multi-layer WHOIS contact harvester resolving authoritative IPv4 records and evaluating email spoofing anti-phishing posture (`v=spf1` / `_dmarc`).
    - **🔍 Passive Subdomain Enumeration**: Instant passive discovery via Certificate Transparency (`crt.sh`), HackerTarget, and UrlScan index logs.
    - **🔬 Web Technology, CMS & Site Tree Fingerprinter**: Header, DOM, and structural site tree analyzer detecting CMS platforms, frameworks, and WAFs while parsing `/robots.txt` and `/sitemap.xml` recursively.
    - **⚡ Full Automated Infrastructure & Site Tree Assessment (ALL-IN-ONE)**: Comprehensive master scan that executes WHOIS/DNS audits, passive subdomain enumeration, intelligent subdomain liveness probing, and multi-host site tree fingerprinting automatically. Incorporates **Subdomain Deduplication & Anti-Mirror Analysis** (`check_subdomain_liveness_and_uniqueness`) to probe every discovered subdomain, filter out dead hosts, detect redirects back to the root domain (`mail.domain -> domain`), and identify exact content mirrors (`www.domain`), ensuring site tree and technology analysis is only run on genuinely unique active subdomains without duplicate noise. Outputs unified JSON and TXT reports.
  - **🏛️ Wayback Machine Historical Archive & Deep Corporate Intelligence Recon**: Mine historical CDX archives (`web.archive.org`) in two specialized modes: **Wayback CDX Interactive Dork Builder & Archive Search** (interactive multi-filter wizard enabling precision historical dorking via `inurl:` path keywords, `-exclude` exclusions, `filetype:` extensions, `status:` HTTP codes like 200/403/301, `from/to` date ranges, and direct **Historical Content Grepping (`intext:`)** inside archived raw snapshots via `id_` modifiers) and **Deep Corporate Intelligence Harvesting** (automatically constructing the full historical site tree via CDX API, classifying historical URLs into targeted intelligence categories—*Contacts & Team*, *Partners & Clients*, *Products & Projects*—and extracting historical email addresses, phone numbers, VAT/fiscal IDs, analytics tracking codes, and entity mentions across multi-lingual snapshots without blind 404 guessing).
  - **🐙 GitHub Code & Secret Dorking**: Scan open source GitHub repositories via REST API for leaked API keys, tokens, configuration files, and target domain mentions (supports optional GitHub PAT).
  - **📞 Phone Number OSINT & Footprinting**: 100% offline analysis and formal validation of international phone numbers using `phonenumbers` and internal prefix maps. Automatically constructs strictly grouped Boolean footprint dorks across 4 target categories with instant multi-engine search execution.
  - **📧 Email Address OSINT & Breach Footprinting**: 100% offline parsing and MX mail exchange resolution (`dnspython`) categorizing mail infrastructures. Automatically generates strictly grouped Boolean footprint dorks for data breach spreadsheet leaks, Pastebin dumps, and professional profile mentions.
  - **👤 Username & Social Cross-Platform Footprinting**: Live HTTP status probing across 13 major developer, social, and gaming platforms confirming active profiles in real-time, accompanied by targeted cross-platform boolean dorks.
- **🛡️ Anti-Rate-Limit WAF Evasion & Resilient Fallbacks**: Built-in multi-layer fallback chains and stealth mechanisms. Simulates real desktop browsers via ultra-modern User-Agent pools (`Chrome/126`, `Firefox/127`, `Edge`) and complete Client Hints headers (`Sec-Ch-Ua`, `Sec-Fetch-Dest`, `Accept-Language`). Features dynamic randomized jitter (between search engines and internal retry loops) to prevent WAF rate-limiting and cleanly handles `0 result` queries without triggering CAPTCHA blocks.
- **🛠️ Interactive Dork Builder**: Step-by-step interactive CLI wizard to construct complex queries without memorizing advanced syntax.
- **🎯 Pre-Built Reconnaissance Templates**: Ready-to-use vulnerability and OSINT search templates for exposed configuration files, database dumps, sensitive logs, and login panels.
- **💾 Multi-Format Export**: Export structured search results to **TXT**, **CSV**, or **JSON** for easy integration into automated OSINT pipelines.
- **⚡ Batch Dork Wordlist Automation**: Execute custom or pre-built lists of dorks (`dorks_sample.txt`) in batch mode across multiple engines with automatic target domain scoping and randomized jitter.
- **🔑 Official API Integration & Fallbacks**: Configure official API keys for Google Custom Search, Brave Search, and GitHub (`config.json` or environment variables) for instant, captcha-free scanning.
- **📜 Search History Session Management**: Automatically track past queries, target scopes, and result counts (`history.json`), allowing instant interactive re-execution across any engine.

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/TheRielax/dorky.git
cd dorky
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start & Usage

### Windows Users (1-Click Launcher)
Simply double-click the included `start_dorky.bat` file. It automatically configures the terminal to UTF-8 code pages (`chcp 65001`), activates the Python virtual environment, and executes `dorky.py`.

### Manual CLI Execution
```bash
python dorky.py
```
*(On Windows cmd/PowerShell, if ASCII art renders incorrectly, run `python -X utf8 dorky.py`)*

---

## 🔑 API Keys & GitHub Token Setup (Optional)

DORKY works out-of-the-box using direct web scraping and public search backends (`ddgs`). However, to avoid CAPTCHAs, rate limits, or to access authenticated scanning endpoints (like GitHub code search), you can configure official API keys.

You can configure your keys interactively inside DORKY by selecting **Option [13] (`Official API Keys Configuration`)** from the main menu, or by editing `config.json` / setting environment variables:

- `GITHUB_API_TOKEN` (GitHub Personal Access Token)
- `GOOGLE_API_KEY` & `GOOGLE_CSE_ID` (Google Custom Search API)
- `BRAVE_API_KEY` (Brave Search API)

> [!NOTE]
> **Local Configuration & Session Privacy**: Files such as `config.json` and `history.json` are strictly ignored by Git (`.gitignore`) to prevent accidental leaks of API tokens or search logs. When cloning the repository or running DORKY for the first time, clean local copies of these files are generated automatically. Reference templates showing the expected structure are provided in `config.example.json` and `history.example.json`.

### 🐙 GitHub Personal Access Token Requirements
When using **Option [9] (`GitHub Code & Secret Dorking`)**, unauthenticated requests to GitHub Search API (`/search/code`) are rate-limited to **10 requests per minute**. Adding a GitHub token raises your rate limit to **30 requests per minute** and enables searching within private repositories.

- **Token Type**: You can use either a **Personal Access Token (classic)** or a **Fine-grained Personal Access Token**.
- **Required Privileges / Scopes**:
  - **For Public Repositories (Standard OSINT)**: **No scopes required!**
    - *Classic PAT*: Leave all scope checkboxes **unchecked** (no permissions needed).
    - *Fine-grained PAT*: Select **Public Repositories (read-only)**.
  - **For Private / Organization Repositories**:
    - *Classic PAT*: Check the `repo` scope (`Full control of private repositories`).
    - *Fine-grained PAT*: Select target repositories under **Repository access** and grant **Contents: Read-only** (or **Code: Read-only**) under **Repository permissions**.

---

## 🧭 Search Engine Syntax Comparison

| Operator | Google | DuckDuckGo / Bing | Yandex | Brave Search |
| :--- | :--- | :--- | :--- | :--- |
| **Domain Filter** | `site:domain.com` | `site:domain.com` | `site:domain.com` | `site:domain.com` |
| **File Extension**| `filetype:pdf` | `filetype:pdf` | `mime:pdf` | `filetype:pdf` |
| **Title Match** | `intitle:"login"` | `intitle:"login"` | `title:"login"` | `intitle:"login"` |
| **URL Match** | `inurl:admin` | `inurl:admin` | `url:admin` | `inurl:admin` |
| **Body Text** | `intext:"password"` | `inbody:"password"` | `"password"` | `"password"` |
| **Exact Phrase Match** | `"confidential data"` | `"confidential data"` | `"confidential data"` | `"confidential data"` |
| **Exclusion** | `-wordpress` | `-wordpress` | `~~wordpress` / `-` | `-wordpress` |

---

## 💡 Recommendations & Best Practices

1. **Keep Dependencies Updated**: Search engine HTML layouts and APIs evolve frequently. Periodically run `pip install --upgrade ddgs requests beautifulsoup4 googlesearch-python` to maintain peak scraping reliability.
2. **Use Target Domain Limits**: When executing vulnerability templates, always specify a target domain (`site:target.com`) to avoid noisy global results and stay focused on authorized scope.
3. **Respect Rate Limits**: If querying heavily across all engines sequentially, allow short pauses between search sessions to avoid temporary IP bans from search engine edge firewalls.

---

## ⚠️ Disclaimer
**DORKY** is developed strictly for authorized penetration testing, security research, and defensive OSINT analysis. The authors are not responsible for any misuse or unauthorized actions conducted with this tool. Always obtain explicit permission before scanning or evaluating target infrastructures.
