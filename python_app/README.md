# Avinya (Python edition)

A modular Python rewrite of the Avinya IIT Roorkee eMBA intelligence
platform — originally a single 600KB HTML/JS file. This version is built
entirely in Python: **Streamlit** for the UX, the official **Anthropic
SDK** for LLM calls, a small agent/orchestrator layer, and a real MCP
connector registry.

It was built after a security/reliability review of the original app
(see the project's `AVINYA-BREAK-REPORT.md`) found several real bugs —
a stored-XSS hole, unguarded `JSON.parse` calls that crashed on corrupted
`localStorage`, an advertised Placement Tracker with no working UI entry
point, inconsistent file-upload validation, and a couple of small DOM
bugs. Those findings directly shaped this rewrite's architecture — see
"Design decisions driven by the original's bugs" below.

## Quick start

```bash
cd python_app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your ANTHROPIC_API_KEY
streamlit run main.py
```

Open the URL Streamlit prints (default `http://localhost:8501`). If you
don't set `ANTHROPIC_API_KEY` in `.env`, you can instead paste a key into
the "Connect AI" box in the sidebar — same idea as the original app's
"Connect AI" button.

## Running the tests

```bash
pip install -r requirements.txt   # includes pytest
pytest -q
```

35 unit tests cover the data loaders, storage layer (including the
corrupted-JSON and cross-session-conflict cases), upload validation, the
LLM client's error handling, and the orchestrator's intent classification
— all with the Anthropic API mocked, so no API key or network access is
needed to run them.

## Architecture

```
python_app/
├── main.py                 # Streamlit entrypoint — session/sidebar + tab routing
├── config.py                # Settings (env vars), single source of truth
├── app/
│   ├── data/                # Read-only knowledge base: courses, faculty, formulas, calendar
│   │   ├── assets/*.json    #   extracted verbatim from the original app's data
│   │   ├── models.py        #   Course / Faculty / Formula dataclasses
│   │   └── loader.py        #   corruption-safe JSON loading + search helpers
│   ├── llm/
│   │   ├── client.py        # AnthropicClient — one call site, timeouts, typed errors
│   │   └── prompts.py       # System prompts, ported from the original (same grounding data)
│   ├── mcp/
│   │   └── registry.py      # MoSPI / Indeed / Consensus / Morningstar MCP connector registry
│   ├── agents/
│   │   ├── base.py          # AgentMeta / TraceEvent / OrchestratorResult types
│   │   └── orchestrator.py  # Intent classification -> agent "trace" + one grounded LLM call
│   ├── storage/
│   │   └── store.py         # Per-student JSON file store, replaces localStorage
│   ├── security/
│   │   └── sanitize.py      # escape_html() + the *one* upload-validation function
│   └── ui/                  # One module per feature/tab (Streamlit widgets only, no business logic)
└── tests/                    # 35 tests, all mocked — no API key needed to run them
```

### Why Streamlit, and what "agents" and "MCP" actually mean here

The original app's 11 "agents" (Orchestrator, IITR KB, Web Search,
LinkedIn, Statista, Scholar, MoSPI, Indeed, Consensus, Morningstar, Deep
Web) were not independent autonomous loops — they were a keyword-based
classifier over a *single* Claude call, which lit up UI pills and picked
which tool (web search or a specific MCP connector) to attach. That
architecture was simple, cheap, and worked, so this rewrite keeps it
honestly rather than pretending to bolt on real multi-agent autonomy the
original never had. `app/agents/orchestrator.py` is the one place that
does this: `classify_intent()` ports the original's regex heuristics,
and `Orchestrator.answer()` makes the one actual model call, attaching
real MCP connectors (`app/mcp/registry.py`, via the Anthropic Messages API
`mcp_servers` beta parameter) when in direct-API-key mode, or falling back
to the `web_search` tool otherwise — same fallback behaviour as the
original.

### Design decisions driven by the original's bugs

- **No `unsafe_allow_html=True` with LLM- or user-derived text, anywhere.**
  The original's stored-XSS bug existed because several `innerHTML`
  assignments interpolated raw model output with no escaping. Streamlit's
  `st.markdown`/`st.write` don't render HTML unless you opt in with
  `unsafe_allow_html=True`; this codebase simply never does that with
  dynamic text. `escape_html()` exists for the rare static-HTML case.
- **One upload validation function, one call site per upload widget.**
  The original had two upload code paths with different (and one with no)
  validation. `app/security/sanitize.py::validate_upload()` is the only
  validator, and `document_intel.py` is the only upload entry point.
- **`safeParse`-style loading everywhere in `app/storage/store.py::load()`.**
  A corrupted or missing profile file returns a fresh default instead of
  raising — the original had ~50 unguarded `JSON.parse(localStorage...)`
  call sites that could crash the page on one bad value.
- **Optimistic-concurrency writes instead of silent last-write-wins.**
  The original silently lost a student's notes when two tabs/sessions
  edited the same profile concurrently. `StudentStore.save()` here checks
  an `expected_version` and raises `ConflictError` on a stale write; the
  UI catches that and tells the student their data changed elsewhere,
  instead of clobbering it invisibly.
- **A request timeout on every LLM call.** The original had no
  client-side timeout at all, so a hung backend spun the UI forever with
  zero feedback. `AnthropicClient` sets an explicit 30s timeout and always
  returns a typed `LLMResult(ok=False, error=...)` on failure.
- **The Placement Tracker actually has a UI.** In the original, the
  add/save/delete JS was fully implemented but referenced DOM ids that
  didn't exist anywhere in the shipped HTML — the feature was advertised
  but unreachable. `app/ui/placement_tracker.py` is a real, working form.

## What's implemented vs. what's a deliberate simplification

Implemented and working: Dashboard, Study (course browser + per-course
notes + formula reference), Faculty directory + AI-enhanced bio lookup,
AI Assist chat, Major Advisor, Case Study Generator, Document
Intelligence (PDF/image upload with validation), Calendar, Live Search,
Placement Tracker, Pomodoro.

Not ported (out of scope for this pass, would need real design/API
access rather than being cheap follow-ons): the Supabase/JSONBin
cross-device sync layer, the "Cohort Library" crowd-sharing feature (it
posts to a live, unauthenticated Google Apps Script endpoint in the
original — deliberately not reproduced here), and the browser-side
TensorFlow.js weakness-prediction model (this rewrite doesn't need a
client-side ML fallback since there's a real Python process to run
anything equivalent in, if that feature is wanted later).

## Data provenance

`app/data/assets/*.json` were extracted directly from the original app's
`COURSE_KB`, `FACULTY`, `FORMULA_DB`, `EVENTS`, and `MCP_SERVERS`
JavaScript objects (33 courses, 28 faculty, 30 formulas, 28 calendar
events, 4 MCP servers — counts match the original's README exactly), so
the reference content is unchanged; only the code that serves it is new.
