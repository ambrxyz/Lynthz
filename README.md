# Lynthz — Multi-model AI Agent v2.0

A fast, intelligent AI assistant with multi-model routing, structured search, 3-tier memory, and a white ambient liquid glass UI.

## Models
| Key | Model | Best For |
|---|---|---|
| Auto | Smart router | Picks the best model automatically |
| `llama` | Llama 3.3 70B (Groq) | Fast chat, general tasks |
| `deepseek` | DeepSeek R1 (Groq) | Reasoning, analysis, math |
| `gemini` | Gemini 2.0 Flash | Search, long context, vision |
| `mixtral` | Mixtral 8x7B (Groq) | Multilingual, balanced |

## Setup

### 1. Clone & install
```bash
git clone <your-repo>
cd lynthz
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables
Copy `.env.example` to `.env` and fill in your keys:
```
GROQ_API_KEY=        # groq.com — free tier, fast
GEMINI_API_KEY=      # aistudio.google.com — free tier
TAVILY_API_KEY=      # tavily.com — 1000 free searches/month
WEATHER_API_KEY=     # openweathermap.org — free tier
```

### 3. Run locally
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
Open `http://localhost:8000`

## Deploy to Railway
1. Push to GitHub
2. New project → Deploy from GitHub repo
3. Add all env vars in Railway dashboard
4. Done — Railway uses `nixpacks.toml` automatically

## Architecture
```
src/
├── api.py          FastAPI + WebSocket streaming
├── agent.py        Brain: intent detection + tool routing  
├── llm_hub.py      Multi-model router (Groq + Gemini)
├── memory.py       3-tier memory (short/working/long-term)
├── tools/
│   ├── search.py   Tavily search + structured cards
│   └── weather.py  OpenWeatherMap
└── static/
    └── index.html  White ambient liquid glass UI
```

## Features
- **Auto-routing**: Detects intent and picks the best model
- **Manual model switch**: Pick any model from sidebar mid-conversation
- **Structured search**: Web results shown as clean cards + LLM summary
- **3-tier memory**: Short-term (12 turns) + working context + long-term facts
- **WebSocket streaming**: Tokens stream in real-time
- **Weather cards**: Rich weather display with icons
