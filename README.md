◆ Codelens — AI Code Reviewer

A web app that gives instant, structured, senior-engineer-style code reviews powered by an LLM, with streaming responses, context-aware follow-up chat, and a built-in voice assistant.

🔗 Live app: codelens-ai-reviewer.streamlit.app


*What it does

Paste or upload a code file → get back a structured review covering bugs, security risks, style, and performance — each issue tagged with severity (HIGH/MEDIUM/LOW) — in seconds, streamed live as it's generated.

After the review, you can ask follow-up questions in a chat ("explain issue 2", "show me the fixed code") and the AI remembers the original code and its own review as context.

There's also a separate Voice Assistant tab — a general-purpose voice Q&A feature with speech-to-text input and spoken responses, built entirely on free browser APIs.

*Features


🔍 Structured AI code review — bugs, security, style, performance, each with severity + fix suggestions
📁 File upload with automatic language detection from file extension
📦 Automatic chunking for large files that exceed a single LLM context window
⚡ Streaming responses — review text appears live, word by word
💬 Context-aware follow-up chat — ask questions about the review, AI remembers the original code
🎙️ Voice input/output — speak your questions, hear the answers, using the browser's free Web Speech API
🎨 Custom dark "diagnostics panel" UI — designed to feel like an IDE linter, not a generic chat form


*Tech stack

Layer              Tool
Language           Python 3.9+
LLML               lama 3.3 70B via Groq API (free tier)
Frontend / UI      Streamlit + custom CSS
Voice (STT / TTS)  Browser Web Speech API — no key, no cost
Env management     python-dotenv (local) · Streamlit Secrets (cloud)
Version control    Git + GitHub
Deployment         Streamlit Community Cloud

*Project structure

codelens-ai-reviewer/
├── app.py             # Main Streamlit app — UI, review logic, chat, voice
├── file_utils.py      # Language detection + chunking for large files
├── voice_utils.py     # Browser-based speech-to-text and text-to-speech components
├── requirements.txt   # Python dependencies
└── .gitignore

*How the review prompt works

The core of this project is a structured prompt that gives the LLM a clear role (senior engineer), specific categories to check (bugs/security/style/performance), and a strict output format — so every review comes back consistent and parseable, not free-form prose. See app.py for the full system prompt.

*What I learned building this

Designing prompts with explicit roles, scope, and output format for consistent LLM responses
Handling LLM rate limits and token-per-minute constraints in a real application
Chunking strategy for content that exceeds an LLM's context window
Streaming LLM responses into a live UI
Managing conversation context/memory across follow-up turns
Browser-native speech APIs (Web Speech API) for free voice features
Secure secrets management across local dev (.env) and cloud deployment (Streamlit Secrets)
Git history hygiene — including recovering from an accidentally committed .env file via git filter-repo and key rotation
