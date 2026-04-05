# Agentic Search

This repository is a submission for the **Agentic Search Challenge** (see challenge text below). It turns a **topic query** into a **structured table of entities** with attributes, backed by **web sources** and **LLM extraction**.

---

## Challenge specification

The following is the task as specified for the challenge.

**Goal.** Build a system that takes a topic query (for example, “AI startups in healthcare”, “top pizza places in Brooklyn”, “open source database tools”) and produces a **structured table of discovered entities** with **relevant attributes**, **sourced from the web**.

**Minimum requirements**

1. Accept a topic query.
2. Search the web for relevant results (any search API: Brave, SerpAPI, etc.).
3. Scrape and process web pages from search results.
4. Use LLMs to extract structured entity data from the scraped content.
5. Return a table of results in a structured format (JSON or rendered).
6. Each cell value should be traceable to its source.

**Guidelines**

- The solution may include a web API, a frontend, or both.
- Any language or framework is fine.
- Any LLM API may be used (OpenRouter, OpenAI, local models, etc.).
- AI coding tools may be used for development.

**How submissions are evaluated**

- **Output quality:** Do the results make sense? Are they accurate and useful for real queries? Are latency and cost reasonable for a real system?
- **Design choices:** What problems were identified and how were they solved? What trade-offs were made?
- **Code structure:** Is the codebase well-organized and readable?
- **Documentation:** Clear setup instructions, explanation of approach, and known limitations.
- **Complexity of implementation:** How far beyond the basics does the solution go?

**Submission requirements**

- Include a **README** with documentation: **description of your approach**, **design decisions you made**, **known limitations**, and **setup instructions**.
- Including a **URL for a live demo** on a free-tier cloud instance is **encouraged**.
- Share code via a **public GitHub repository** and send an email to **csamarinas@umass.edu** with this **exact** subject line: `CIIR challenge submission`.

**Deadline:** Saturday, April 4th at 11:59 PM EDT.

---

## How this project meets the minimum requirements

| Requirement | Implementation |
|-------------|----------------|
| Topic query | **CLI:** `agentic-search "your query"` or `python -m agentic_search "your query"`. **HTTP API:** `POST /search` with JSON `{"query": "..."}`. |
| Web search | Pluggable retrievers: **Brave Search API**, **SerpAPI** (Google), or **fixture** (fixed URLs for smoke tests). Selected via `SEARCH_PROVIDER` in `.env`. |
| Scrape and process pages | URLs are fetched over HTTP; main article text is extracted with **trafilatura** (not raw HTML). Long pages are **chunked** for the LLM. |
| LLM structured extraction | OpenAI-compatible **chat completions** with `response_format: json_object`; prompts require entities, attributes, and per-field **sources** (URL + quote). |
| Structured table (JSON or rendered) | **JSON:** `entities` (rows), each with `attributes` mapping column names to `{ value, sources[] }`. **Web UI:** open `/` after starting `uvicorn` to enter a query and view an HTML table with source links per cell. CLI `--json` prints the full payload. |
| Traceable cells | Each attribute value includes **`sources`**: `{ url, quote }` tying the value to scraped content. |

**Guidelines in this repo:** Implementation is **Python** with **FastAPI** (REST + static UI at `/`), a **CLI**, and a minimal **web UI** (`static/index.html`). The LLM uses **`OPENROUTER_API_KEY`** (OpenRouter) or **`OPENAI_API_KEY`** (OpenAI), plus **`OPENAI_BASE_URL`** and **`OPENAI_MODEL`** as needed.

---

## Approach

1. **Search** — Run the configured search API and collect top URLs (title + snippet).
2. **Fetch** — Download each page and extract readable text.
3. **Chunk** — Split long text so each LLM request stays within context limits.
4. **Extract** — For each chunk, call the LLM to produce JSON: entity names, dynamic attribute columns suited to the topic, and provenance for each cell.
5. **Merge** — Normalize entity names and merge duplicate rows, unioning sources.

Configuration is loaded from **`.env`** at the project root (next to `pyproject.toml`), so keys are not committed.

---

## Design decisions and trade-offs

| Topic | Decision | Trade-off |
|-------|-----------|-----------|
| Search provider | Abstract `Retriever` + env-selected backend | Easy to swap Brave vs SerpAPI; each has its own quota and pricing. |
| Extraction | One LLM call per text chunk | Simpler and robust to long pages; higher **cost** and **latency** than a single call per URL. |
| Provenance | Require `sources` with URL + quote in the schema | Better accountability; quotes can be wrong or truncated if the model drifts. |
| Merge | Normalize names and merge attributes | Reduces duplicate entities; risk of over-merging similarly named entities. |
| API surface | FastAPI + CLI + static web UI | JSON remains the contract; UI is a thin viewer over `/search`. |

---

## How this documentation addresses the evaluation criteria

- **Output quality:** Results depend on search quality, page extractability, and the LLM. Tune `TOP_K_URLS`, model choice, and prompts. See **Manual evaluation (task examples)** below for a concrete run; some sites block scrapers (**HTTP 403**) or return little extractable text.
- **Design choices:** See the table above and **Known limitations**.
- **Code structure:** Pipeline is split under `src/agentic_search/pipeline/` (`search`, `fetch`, `chunk`, `extract`, `merge`, `run`); settings in `config.py`; schemas in `models/schemas.py`.
- **Documentation:** This README provides **setup**, **approach**, and **limitations** as required.
- **Complexity beyond basics:** Pluggable search backends, chunked extraction, merge with provenance, optional HTTP API—not only a single script.

---

## Setup instructions

```bash
cd AgenticSearch
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -e ".[dev]"
copy .env.example .env
# Edit .env: SEARCH_PROVIDER, SerpAPI/Brave key, then OPENROUTER_API_KEY or OPENAI_*.
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `SEARCH_PROVIDER` | `brave`, `serpapi`, or `fixture` |
| `BRAVE_API_KEY` | [Brave Search API](https://brave.com/search/api/) |
| `SERPAPI_KEY` | [SerpAPI](https://serpapi.com/) when using `serpapi` |
| `OPENROUTER_API_KEY` | If set, LLM requests go to [OpenRouter](https://openrouter.ai/) (default base URL `https://openrouter.ai/api/v1`). Overrides use of `OPENAI_API_KEY` for auth. |
| `OPENAI_API_KEY` | Direct OpenAI API key (used when `OPENROUTER_API_KEY` is empty). |
| `OPENAI_BASE_URL` | Override LLM base URL. If `OPENROUTER_API_KEY` is set and this is still the default OpenAI URL, the app uses OpenRouter’s base URL instead. |
| `OPENAI_MODEL` | Model id (e.g. `gpt-4o-mini` for OpenAI, or `openai/gpt-4o-mini` on OpenRouter). |
| `OPENROUTER_HTTP_REFERER` | Optional; OpenRouter may use this header for analytics. |
| `OPENROUTER_X_TITLE` | Optional app name sent as `X-Title` to OpenRouter (default `AgenticSearch`). |
| `TOP_K_URLS` | Max URLs to fetch (default `8`) |

### How to run the project

From the repository root (the folder that contains `pyproject.toml`):

```bash
python -m venv .venv
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env
# Edit .env: search API key, OPENROUTER_API_KEY or OPENAI_*, OPENAI_MODEL (e.g. openai/gpt-4o-mini on OpenRouter).
```

**Option A — Web UI (topic query → table with sources)**  
Start the server, then open the app in a browser:

```bash
uvicorn agentic_search.api.main:app --reload --host 127.0.0.1 --port 8000
```

- **UI:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — enter a query and view the results table; each cell links to sources.
- **API:** `POST /search` with JSON `{"query": "..."}` — same payload as the CLI `--json` output.
- **Health:** `GET /health`

**Option B — CLI** (summary; add `--json` for the full JSON):

```bash
agentic-search "open source vector databases"
agentic-search "open source vector databases" --json
```

### Live demo (optional, encouraged)

Deploy the FastAPI app to a free-tier host (for example Render, Fly.io, Railway), set **environment variables** there (not in the repo), and add the public **HTTPS URL** to this README when available.

---

## Manual evaluation (task examples)

The challenge text suggests example queries such as **“AI startups in healthcare”**, **“top pizza places in Brooklyn”**, and **“open source database tools”**. The script `scripts/run_task_examples.py` runs all three with **`TOP_K_URLS=3`** (overridden in the script for faster, cheaper checks; increase **`TOP_K_URLS`** in `.env` for fuller tables in production).

```bash
# From the repo root (folder with pyproject.toml):
# Windows CMD:
set PYTHONPATH=src
python scripts/run_task_examples.py
# PowerShell:
# $env:PYTHONPATH = "src"; python scripts/run_task_examples.py
```

This prints a JSON summary and writes **`evaluation_runs.json`** (gitignored). Re-run anytime after changing prompts or search settings.

### Results (one representative run)

| Example query | Entities extracted (approx.) | Notes |
|---------------|------------------------------|--------|
| AI startups in healthcare | 14 | One top URL returned **HTTP 403** (site blocks automated fetch). Other pages still yielded rows; some “entity” names read as **product phrases** (e.g. capability lines)—acceptable for demo but worth human skim for nonsense. |
| top pizza places in Brooklyn | 0 | **All** fetched URLs failed: **403** on magazine/Tripadvisor-style pages, **little text** on Reddit. No text for the LLM ⇒ empty table—not a model bug, but **sparse/fragile** evidence for this query unless search returns more fetchable URLs. |
| open source database tools | 2 | Example entities included **DBeaver**, **PostgreSQL**; one Reddit URL had little extractable text. |

**Skim for nonsense:** Check that values match the quoted snippets; watch for over-merged entities or generic phrases listed as “entities.” **403 / thin pages are normal** for open-web scraping: many sites block or challenge non-browser clients.

**Getting fuller tables:** Raise **`TOP_K_URLS`** (e.g. 8–12) so SerpAPI/Brave returns more URLs—if more pages succeed, the model has more evidence. **Optional future work:** rerank search hits (e.g. by snippet relevance or domain allowlist) before fetch, or retry with alternate queries if most URLs fail.

---

## Known limitations

- **Billing / quota:** OpenAI may return **401** (invalid key) or **429** (quota or rate limits). Use **`OPENROUTER_API_KEY`** and an OpenRouter model id (e.g. `openai/gpt-4o-mini`) if OpenAI billing is an issue, or add credits on the OpenAI account.
- **Cost and latency:** Multiple LLM calls per query (per chunk × pages); reduce `TOP_K_URLS` or chunk size for cheaper runs.
- **Scraping and scraper blocks:** Many sites return **HTTP 403**, use bot protection, or serve **little extractable text** (e.g. Reddit, listings behind anti-bot, heavy JavaScript). That is **expected** for a simple HTTP + trafilatura client—not a bug in the pipeline. Respect **robots.txt** and **terms of service** for real deployments.
- **Hallucinations:** Despite quote-based prompts, the model can still invent or misattribute facts; a verification pass would strengthen production use.
- **Fixture mode:** No real web search—only for wiring tests without search API keys.

---

## Project layout

```
src/agentic_search/
  config.py          # Settings from .env
  static/index.html  # Simple web UI (served at /)
  models/schemas.py  # SearchHit, EntityRow, AttributeCell, SourceRef, PipelineResult
  pipeline/
    search.py        # Retriever implementations
    fetch.py         # HTTP + trafilatura
    chunk.py         # Text chunks for the LLM
    extract.py       # LLM JSON extraction
    merge.py         # Entity dedupe + source union
    run.py           # Orchestration
  api/main.py        # FastAPI
  cli.py             # CLI entry point
scripts/
  run_task_examples.py  # Runs the three challenge example queries; writes evaluation_runs.json
```

---

## Submission checklist (CIIR)

- [ ] Public **GitHub** repository with this code.
- [ ] This **README** includes approach, design decisions, limitations, and setup (per challenge).
- [ ] Email **csamarinas@umass.edu** with subject line exactly: **`CIIR challenge submission`**
- [ ] (Optional) **Live demo URL** added above once deployed.

---

## License

MIT (adjust as needed for your submission.)
