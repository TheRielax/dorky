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
  - **🌐 Passive Subdomain Enumeration**: Instant passive subdomain discovery querying Certificate Transparency logs (`crt.sh`) with zero target interaction and direct dork pipeline integration.
  - **🏛️ Wayback Machine Archive Explorer**: Mine historical CDX archives (`web.archive.org`) to discover forgotten endpoints, old `.env` files, database dumps, and past administrative panels.
  - **🐙 GitHub Code & Secret Dorking**: Scan open source GitHub repositories via REST API for leaked API keys, tokens, configuration files, and target domain mentions (supports optional GitHub PAT).
  - **🔬 Web Technology & CMS Fingerprinter**: Lightweight HTTP header & DOM analyzer detecting CMS platforms (WordPress, Joomla, Drupal), Frontend frameworks (React, Next.js, Vue), Backends (PHP, Laravel, Django), and WAFs (Cloudflare).
  - **📞 Phone Number OSINT & Footprinting**: 100% offline analysis and formal validation of international phone numbers using `phonenumbers` and internal prefix maps (identifying E.164 validity, region/location, line type, timezones, and original ministerial carrier block allocation). Automatically constructs strictly grouped Boolean footprint dorks across 4 target categories (general web formatting, Telegram/WhatsApp/social profiles, spam/reputation directories, and PDF/TXT/Pastebin document leaks) with instant multi-engine search execution.
- **🛡️ Anti-Rate-Limit & Resilient Fallbacks**: Built-in multi-layer fallback chains powered by `ddgs` and direct scraping. If an engine imposes rate limits or CAPTCHAs, DORKY seamlessly pivots across clean backends while validating output URLs to reject ad-tracking redirects.
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

You can configure your keys interactively inside DORKY by selecting **Option [12] (`Official API Keys Configuration`)** from the main menu, or by editing `config.json` / setting environment variables:

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
