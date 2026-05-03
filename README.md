# Avinya — IIT Roorkee eMBA AI Platform

> Next-generation AI learning platform for DoMS IITR students  
> Built with Anthropic Claude · Deployed on GitHub Pages + Render

## Live App

**Frontend:** `https://YOUR-USERNAME.github.io/avinya`  
**Backend:** `https://avinya-proxy.onrender.com`

---

## Repository Structure

```
avinya/
├── index.html              ← Full Avinya SPA (all features, 402 KB)
├── README.md               ← This file
├── backend/
│   ├── avinya_server.py    ← Python proxy server (no dependencies)
│   ├── render.yaml         ← Render deployment config
│   ├── railway.json        ← Railway deployment config
│   └── Dockerfile          ← Docker config (any platform)
└── .github/
    └── workflows/
        └── deploy.yml      ← Auto-deploy to GitHub Pages on push
```

---

## Deploy in 3 Steps

### Step 1 — Fork and enable Pages

1. Fork this repo on GitHub  
2. Go to **Settings → Pages → Source → GitHub Actions**  
3. Push any change — GitHub automatically deploys `index.html` to Pages

### Step 2 — Deploy the Python backend on Render

1. Go to [render.com](https://render.com) → **New Web Service**  
2. Connect this GitHub repo  
3. Set **Root Directory** to `backend`  
4. **Build command:** *(leave blank)*  
5. **Start command:** `python avinya_server.py`  
6. **Environment Variables → Add:**  
   - `ANTHROPIC_KEY` = `sk-ant-YOUR-KEY`  
7. Deploy — Render gives you `https://avinya-proxy.onrender.com`

### Step 3 — Connect frontend to backend

Edit `index.html` line 1 of the JS section:

```js
// Change from:
let PROXY_URL = localStorage.getItem('avinya_proxy') || 'https://avinya-proxy.onrender.com';

// To your actual Render URL if different:
let PROXY_URL = localStorage.getItem('avinya_proxy') || 'https://YOUR-SERVICE.onrender.com';
```

Push → GitHub Actions redeploys automatically.

---

## Features

| Feature | Description |
|---|---|
| **8 Tabs** | Dashboard · Study · Cases · AI Assist · Major Advisor · Faculty · Calendar · Live Search |
| **33 Courses** | Full DoMS IITR curriculum T1–T7 with verified professor mapping |
| **28 Faculty** | Research areas, contact info, AI-enhanced LinkedIn profiles |
| **Adaptive Engine** | Personalised study plans from quiz history + Pomodoro data |
| **Document Intel** | Upload PDF/image → AI generates notes, questions, summary, formulas |
| **Case Generator** | HBS · MIT Sloan · Stanford · INSEAD · DoMS IITR styles |
| **11 AI Agents** | Orchestrator, IITR KB, Web Search, LinkedIn, Statista, Patents, Scholar, MoSPI, Indeed, Consensus, Morningstar |
| **Pomodoro + Notes** | Per-course notes with auto-save, AI enhance, export |
| **Formula Reference** | 30+ formulas across Finance, OR, Stats, Strategy with search |
| **Placement Tracker** | Application tracking + live Indeed job search |
| **Major Advisor** | Specialisation recommendation with live market intelligence |

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR-USERNAME/avinya.git
cd avinya

# Run locally with Python (zero dependencies)
ANTHROPIC_KEY=sk-ant-YOUR-KEY python backend/avinya_server.py

# Then open http://localhost:3000
# (points to index.html in repo root via the server)
```

Or just open `index.html` directly in a browser and use the  
"Connect AI" button to paste your own API key.

---

## Updating

When a new `index.html` is released:
1. Replace `index.html` in the repo root  
2. Push to `main`  
3. GitHub Actions deploys automatically in ~30 seconds

The `backend/avinya_server.py` rarely needs updating — it's a  
thin 109-line proxy with no business logic.

---

## Cost

Using `claude-sonnet-4-6`:
- Quiz / flashcard: ~$0.001 per session
- Case study: ~$0.006
- Document analysis: ~$0.009
- Heavy day per student: ~$0.05–0.15

Anthropic free tier ($5 credit) ≈ 50–100 full sessions.
