# 🤖 ClawdBot Hub

**One Interface, All AI Models** - A multi-model AI gateway that intelligently routes your queries to the best AI for the job.

![ClawdBot Hub](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18-blue)

## 🚀 Features

- **Intelligent Routing**: Automatically selects the best AI model based on your query type
- **Multi-Provider Support**: Claude, GPT-4, Gemini, HuggingFace, Perplexity
- **Unified Interface**: One chat interface for all AI models
- **Real-time Streaming**: Stream responses as they're generated
- **Category Detection**: Automatically classifies queries (coding, research, creative, etc.)

## 📊 Supported Providers

| Provider | Best For | Models |
|----------|----------|--------|
| 🧠 Claude | Reasoning, Analysis, Coding | claude-3-opus, claude-3-sonnet |
| 💚 OpenAI | General, Creative, Coding | gpt-4-turbo, gpt-4 |
| 💎 Gemini | Multimodal, Research | gemini-pro |
| 🤗 HuggingFace | Specialized Tasks | 1000s of models |
| 🔍 Perplexity | Real-time Search, Research | pplx-70b-online |

## 🛠️ Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for at least one provider

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env
# Edit .env and add your API keys

# Run the server
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the App

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 🔑 API Keys Setup

Get your API keys from:

- **Anthropic (Claude)**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys
- **Google (Gemini)**: https://makersuite.google.com/app/apikey
- **HuggingFace**: https://huggingface.co/settings/tokens
- **Perplexity**: https://www.perplexity.ai/settings/api

## 📡 API Endpoints

### POST /chat
Send a message and get an AI response.

```json
{
  "message": "Write a Python function to sort a list",
  "conversation_history": [],
  "preferred_provider": null
}
```

### GET /providers
List all configured providers and their status.

### POST /chat/stream
Stream a response using Server-Sent Events.

## 🧠 How Routing Works

ClawdBot analyzes your query and routes to the best provider:

1. **Coding queries** → Claude, OpenAI
2. **Research/Search** → Perplexity, Gemini
3. **Creative writing** → Claude, OpenAI
4. **Analysis** → Claude, OpenAI
5. **Health info** → Perplexity, Claude
6. **Business** → Claude, OpenAI

## 📁 Project Structure

```
clawdbot-hub/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── router.py        # Query routing logic
│   │   └── providers/       # AI provider integrations
│   │       ├── base.py
│   │       ├── claude_provider.py
│   │       ├── openai_provider.py
│   │       ├── gemini_provider.py
│   │       ├── huggingface_provider.py
│   │       └── perplexity_provider.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Deployment

### Backend (Railway/Render/Fly.io)

```bash
# Build command
pip install -r requirements.txt

# Start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy dist/ folder
```

## 📝 License

MIT License - feel free to use this for your projects!

## 🤝 Contributing

Pull requests welcome! Please read our contributing guidelines first.

---

Built with ❤️ by the ClawdBot Team
