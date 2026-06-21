import os
import re
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
from file_utils import detect_language, chunk_code, needs_chunking
from voice_utils import mic_button, voice_chat_widget, speak_text, stop_speaking_button

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error(
        "GROQ_API_KEY not found. Locally: add it to your .env file. "
        "On Streamlit Cloud: add it under Settings → Secrets."
    )
    st.stop()

client = Groq(api_key=groq_api_key)

st.set_page_config(page_title="Codelens — AI Code Review", page_icon="◆", layout="wide")

SYSTEM_PROMPT = """You are a senior software engineer doing a thorough code review.

For the code provided, analyze it across these categories:
1. BUGS - logic errors, edge cases, potential crashes
2. SECURITY - injection risks, hardcoded secrets, unsafe operations
3. STYLE - readability, naming, formatting issues
4. PERFORMANCE - inefficiencies, unnecessary complexity

Output your review in this exact format:

## Summary
(1-2 sentence overall verdict)

## Issues Found
For each issue, use this format:
- [SEVERITY: HIGH/MEDIUM/LOW] [CATEGORY] Description of the issue
  Suggestion: how to fix it

## What's Good
(briefly note anything done well)

If there are no issues in a category, skip it. Be specific and reference line numbers
or exact code where possible. Be concise — no fluff."""

CHAT_SYSTEM_PROMPT = """You are a senior software engineer who just reviewed a piece of code.
The user may now ask follow-up questions about your review or the code itself
(e.g. "explain issue 2", "show me the fixed version", "why is this a security risk").
Answer clearly and concisely, referencing the original code and your review when relevant."""

ASSISTANT_SYSTEM_PROMPT = """You are a friendly, knowledgeable general-purpose assistant.
The user is speaking to you by voice, so keep answers conversational, clear, and
reasonably concise — a few sentences for simple questions, more only if the question
genuinely needs depth. Avoid heavy markdown formatting like tables or code blocks
unless the user specifically asks for code, since your answer will be read aloud."""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-deep: #0D1117;
    --bg-panel: #151B23;
    --bg-panel-raised: #1C242E;
    --border-subtle: #2A3340;
    --text-primary: #E6EDF3;
    --text-secondary: #8B95A1;
    --accent-cyan: #4FD1C5;
    --sev-high: #F85149;
    --sev-medium: #E3A008;
    --sev-low: #58A6FF;
    --sev-good: #3FB950;
}

.stApp {
    background: var(--bg-deep);
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit chrome for a cleaner look */
#MainMenu, footer, header { visibility: hidden; }

/* ---- Header / hero ---- */
.codelens-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    padding: 8px 0 4px;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 28px;
}
.codelens-logo {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 26px;
    color: var(--text-primary);
    letter-spacing: -0.02em;
}
.codelens-logo span { color: var(--accent-cyan); }
.codelens-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--text-secondary);
    padding-bottom: 4px;
}

/* ---- Panels ---- */
.panel-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.panel-label::before {
    content: "";
    width: 6px; height: 6px;
    background: var(--accent-cyan);
    display: inline-block;
}

/* ---- Streamlit widget overrides ---- */
.stTextArea textarea {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}
.stTextArea textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 1px var(--accent-cyan) !important;
}
.stSelectbox > div > div {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}
[data-testid="stFileUploader"] {
    background: var(--bg-panel);
    border: 1px dashed var(--border-subtle);
    border-radius: 8px;
    padding: 12px;
}
[data-testid="stFileUploader"] small { color: var(--text-secondary) !important; }

.stButton > button {
    background: var(--accent-cyan) !important;
    color: #0D1117 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-family: 'JetBrains Mono', monospace !important;
    padding: 10px 22px !important;
    transition: transform 0.1s ease, box-shadow 0.15s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 0 0 3px rgba(79, 209, 197, 0.25) !important;
    transform: translateY(-1px);
}

/* ---- Result card ---- */
.result-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 4px;
}
.result-card h2 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-cyan);
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 8px;
    margin-top: 18px;
}
.result-card h2:first-child { margin-top: 0; }

/* Severity badges injected into markdown text */
.sev-high  { background: rgba(248,81,73,0.15); color: var(--sev-high); border: 1px solid rgba(248,81,73,0.4); }
.sev-medium{ background: rgba(227,160,8,0.15); color: var(--sev-medium); border: 1px solid rgba(227,160,8,0.4); }
.sev-low   { background: rgba(88,166,255,0.15); color: var(--sev-low); border: 1px solid rgba(88,166,255,0.4); }
.sev-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
}
.cat-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--bg-panel-raised);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
    margin-right: 8px;
}

/* Token usage chip */
.token-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-secondary);
    background: var(--bg-panel-raised);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 4px 12px;
    display: inline-block;
    margin-top: 12px;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
}
.stChatInput textarea {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
}

/* Info / warning boxes */
.stAlert {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}

/* Empty state */
.empty-state {
    border: 1px dashed var(--border-subtle);
    border-radius: 10px;
    padding: 40px 24px;
    text-align: center;
    color: var(--text-secondary);
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)


def style_review_markdown(text: str) -> str:
    """Inject HTML severity/category badges into the model's markdown output."""
    def replace_issue(match):
        severity = match.group(1).upper()
        category = match.group(2).upper()
        sev_class = {"HIGH": "sev-high", "MEDIUM": "sev-medium", "LOW": "sev-low"}.get(severity, "sev-low")
        return f'<span class="sev-badge {sev_class}">{severity}</span><span class="cat-badge">{category}</span>'

    text = re.sub(r"\[SEVERITY:\s*(HIGH|MEDIUM|LOW)\]\s*\[?([A-Z]+)\]?", replace_issue, text)
    return text


def review_chunk_stream(code: str, language: str):
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\n\nHere is the code to review:\n\n```{language}\n{code}\n```"},
        ],
        max_tokens=800,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def chat_reply_stream(messages: list[dict]):
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=600,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def assistant_reply(question: str) -> str:
    """Non-streaming reply for the voice assistant tab (simpler to speak aloud in one piece)."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=400,
    )
    return response.choices[0].message.content
# UI
st.markdown("""
<div class="codelens-header">
    <div class="codelens-logo">◆ Code<span>lens</span></div>
    <div class="codelens-tagline">// senior-engineer-grade review, in seconds</div>
</div>
""", unsafe_allow_html=True)

tab_review, tab_assistant = st.tabs(["📋  Code Review", "🎙️  Voice Assistant"])

with tab_review:
    col1, col2 = st.columns([3, 1], gap="large")

    with col2:
        st.markdown('<div class="panel-label">Input source</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a file",
            type=["py", "js", "ts", "java", "go", "sql", "txt", "jsx", "tsx", "rb", "cpp", "c", "rs"],
            label_visibility="collapsed",
        )

        detected_lang = "python"
        if uploaded_file is not None:
            detected_lang = detect_language(uploaded_file.name)
            st.caption(f"→ detected: **{detected_lang}**")

        st.markdown('<div class="panel-label" style="margin-top:18px">Language</div>', unsafe_allow_html=True)
        lang_options = ["python", "javascript", "typescript", "java", "go", "sql", "ruby", "cpp", "c", "rust", "other"]
        language = st.selectbox(
            "Language",
            lang_options,
            index=lang_options.index(detected_lang) if detected_lang in lang_options else 0,
            label_visibility="collapsed",
        )

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        review_clicked = st.button("▶  Run review", type="primary", use_container_width=True)

    with col1:
        st.markdown('<div class="panel-label">Code</div>', unsafe_allow_html=True)

        default_code = ""
        if uploaded_file is not None:
            default_code = uploaded_file.read().decode("utf-8")

        code_input = st.text_area(
            "Code",
            value=default_code,
            height=320,
            placeholder="def example():\n    pass",
            label_visibility="collapsed",
        )

        if code_input and needs_chunking(code_input):
            st.info("📦 Large input detected — only the first chunk is reviewed in streaming mode.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if review_clicked:
        if not code_input.strip():
            st.warning("Paste some code or upload a file first.")
        else:
            st.session_state["chat_history"] = []
            st.session_state["reviewed_code"] = code_input
            st.session_state["reviewed_language"] = language

            st.markdown('<div class="panel-label">Review</div>', unsafe_allow_html=True)
            placeholder = st.empty()
            full_text = ""
            try:
                chunk_to_review = chunk_code(code_input)[0]
                for piece in review_chunk_stream(chunk_to_review, language):
                    full_text += piece
                    placeholder.markdown(
                        f'<div class="result-card">{style_review_markdown(full_text)}▌</div>',
                        unsafe_allow_html=True,
                    )
                placeholder.markdown(
                    f'<div class="result-card">{style_review_markdown(full_text)}</div>',
                    unsafe_allow_html=True,
                )
                st.session_state["last_review"] = full_text
            except Exception as e:
                st.error(f"Something went wrong: {e}")

    elif "last_review" in st.session_state:
        st.markdown('<div class="panel-label">Review</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="result-card">{style_review_markdown(st.session_state["last_review"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="empty-state">◆ no review yet — paste code or upload a file, then run review</div>',
            unsafe_allow_html=True,
        )

    # ---------- Follow-up chat ----------
    if "last_review" in st.session_state:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Ask a follow-up</div>', unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        mic_button(key="voice_chat", label="🎤 Ask by voice")
        voice_chat_text = st.query_params.get("voice_chat", "")

        user_question = st.chat_input("e.g. 'Explain the security issue' or 'Show me the fixed code'")

        if not user_question and voice_chat_text:
            user_question = voice_chat_text
            if "voice_chat" in st.query_params:
                del st.query_params["voice_chat"]

        if user_question:
            st.session_state["chat_history"].append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            context_messages = [
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Original code:\n```{st.session_state['reviewed_language']}\n{st.session_state['reviewed_code']}\n```"},
                {"role": "assistant", "content": st.session_state["last_review"]},
            ] + st.session_state["chat_history"]

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_reply = ""
                for piece in chat_reply_stream(context_messages):
                    full_reply += piece
                    placeholder.markdown(full_reply + "▌")
                placeholder.markdown(full_reply)

            st.session_state["chat_history"].append({"role": "assistant", "content": full_reply})

with tab_assistant:
    st.markdown(
        '<div class="panel-label">General voice assistant — ask anything</div>',
        unsafe_allow_html=True,
    )

    if "assistant_history" not in st.session_state:
        st.session_state["assistant_history"] = []

    for msg in st.session_state["assistant_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # mic button
    voice_chat_widget(key="voice_assistant")
    stop_speaking_button(key="stop_assistant_speak")
    voice_assistant_text = st.query_params.get("voice_assistant", "")

    # Also allow typing, for when voice isn't convenient
    typed_question = st.chat_input("Or type your question here")

    spoken_question = None
    if voice_assistant_text:
        spoken_question = voice_assistant_text
        if "voice_assistant" in st.query_params:
            del st.query_params["voice_assistant"]

    final_question = typed_question or spoken_question

    if final_question:
        st.session_state["assistant_history"].append({"role": "user", "content": final_question})
        with st.chat_message("user"):
            st.markdown(final_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply_text = assistant_reply(final_question)
            st.markdown(reply_text)
            speak_text(reply_text, key="assistant_speak")

        st.session_state["assistant_history"].append({"role": "assistant", "content": reply_text})

        st.caption("🔊 Reply spoken aloud automatically. Click the mic above to ask another question.")