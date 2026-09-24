# FENRY-GF: Cyberpunk AI Girlfriend Assistant

A premium, cyberpunk/sci-fi themed full-stack web application for the FENRY personal AI girlfriend assistant. FENRY features neural thinking, persistent memory, voice I/O, persona customization, and comprehensive analytics — entirely powered by local AI running on Ollama (`llama3.2:1b`).

## 🌟 Features

- **Neural Thinking Engine**: Visualizes FENRY's internal thought process (Plan → Act → Reflect → Memorize) in real-time.
- **Cyberpunk UI**: Glassmorphic chat interface with neon accents, dynamic animations, and a responsive layout.
- **Browser-Native Voice I/O**: Push-to-talk microphone and text-to-speech utilizing the Web Speech API (no external services needed).
- **Persistent Vector Memory**: Utilizes ChromaDB to store and retrieve conversation summaries, preferences, and milestones.
- **Affect & Emotion Modeling**: Tracks FENRY's mood, energy, and attachment levels, influencing her conversational tone and behavior.
- **Tool Use Capabilities**: Integrated with tools like Wikipedia and DuckDuckGo for web search capabilities.
- **Analytics Dashboard**: Tracks interaction metrics, mood gauges, conversation history heatmaps, and topics using Recharts.
- **Persona Customization**: Edit FENRY's personality, boundaries, and preferences dynamically via a dedicated settings page.

## 🏗️ Architecture & Tech Stack

The application is completely local and does not require external API keys for its core functionalities.

### **Frontend**
- **Framework**: React 18 + Vite (SPA)
- **Styling**: Custom Cyberpunk CSS Design System (Vanilla CSS)
- **Routing**: React Router
- **Data Visualization**: Recharts
- **Voice Capabilities**: Web Speech API

### **Backend**
- **Framework**: Python FastAPI + Uvicorn (REST API & WebSocket Server)
- **LLM Engine**: Ollama (`llama3.2:1b`) with a dual connection strategy (`ollama` library + `httpx` fallback)
- **Vector Store (Memory)**: ChromaDB
- **Database (Analytics)**: SQLite
- **Tooling**: `duckduckgo-search`, `wikipedia`

## 🚀 Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.10+)
- [Ollama](https://ollama.com/) (Make sure it's installed and running)

### 1. Setup Local AI Model (Ollama)
Pull the required model for FENRY before running the application:
```bash
ollama pull llama3.2:1b
```

### 2. Backend Setup
Navigate to the `backend` directory, create a virtual environment, and install dependencies:
```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
```

Run the FastAPI server:
```bash
python main.py
# Or using uvicorn directly
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
Open a new terminal, navigate to the `frontend` directory, and install dependencies:
```bash
cd frontend
npm install
```

Start the Vite development server:
```bash
npm run dev
```

### 4. Access the Application
Open your browser and navigate to the URL provided by Vite (usually `http://localhost:5173`).

## 📂 Project Structure

```text
AI-GF Assistant/
├── backend/                   # FastAPI Backend
│   ├── core/                  # Neural engine, LLM connection, memory store, tools
│   ├── data/                  # SQLite DB and ChromaDB storage
│   ├── models/                # Pydantic models & DB schemas
│   ├── persona/               # GF persona configuration (YAML)
│   ├── routers/               # API & WebSocket endpoints
│   ├── config.py              # Environment configurations
│   ├── main.py                # FastAPI entry point
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React + Vite Frontend
│   ├── public/                # Static assets (fonts, etc.)
│   ├── src/                   # Source code
│   │   ├── components/        # Reusable UI components (Sidebar, ChatArea, etc.)
│   │   ├── hooks/             # Custom React hooks (WebSockets, Voice, etc.)
│   │   ├── pages/             # App pages (Chat, Analytics, Memory, etc.)
│   │   ├── utils/             # API helpers and constants
│   │   ├── App.jsx            # Application root
│   │   ├── index.css          # Cyberpunk design system
│   │   └── main.jsx           # React entry point
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Vite configuration
└── .env                       # Global environment vfenrybles
```

## 🧠 Memory & Analytics
- **ChromaDB** is used to create a semantic search index of the conversation history, allowing FENRY to remember past events and user preferences across sessions.
- **SQLite** logs interactions and mood states, serving the rich analytics dashboard.

## 🛠️ Customization
To customize FENRY's personality, navigate to the **Persona Editor** in the UI, or manually edit the `backend/persona/gf_model.yaml` file. Changes can be made to her affection levels, verbosity, emoji usage, and specific boundaries.

## 📝 License
This project is for personal use and experimentation with local LLMs and full-stack integration.
