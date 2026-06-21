"""
Browser-based speech-to-text using the Web Speech API (built into Chrome/Edge).
No API key, no cost, no extra Python package - runs entirely in the user's browser.

How it works: we render a small HTML/JS component with a mic button. When clicked,
it listens, transcribes speech to text using the browser's built-in engine, then
writes the result into a hidden Streamlit text input via streamlit's component
communication, which we read back into session_state.
"""

import streamlit.components.v1 as components


def mic_button(key: str, label: str = "🎤") -> str:
    """
    Renders a microphone button. Returns transcribed text via session_state[key]
    once the browser captures speech. Uses localStorage + polling since
    Streamlit's custom component protocol requires a registered component for
    full bidirectional communication - this lightweight version uses the
    simpler postMessage + query param approach instead.
    """
    component_html = f"""
    <div style="display:flex;align-items:center;gap:8px;">
        <button id="mic-btn-{key}" onclick="startListening_{key}()"
            style="background:#1C242E;border:1px solid #2A3340;color:#4FD1C5;
                   border-radius:6px;padding:8px 14px;cursor:pointer;
                   font-family:'JetBrains Mono',monospace;font-size:13px;">
            {label} Speak
        </button>
        <span id="mic-status-{key}" style="font-family:'JetBrains Mono',monospace;
              font-size:12px;color:#8B95A1;"></span>
    </div>
    <script>
    function startListening_{key}() {{
        const statusEl = document.getElementById("mic-status-{key}");
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            statusEl.innerText = "Speech recognition not supported in this browser. Try Chrome.";
            return;
        }}
        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        statusEl.innerText = "Listening...";
        recognition.start();

        recognition.onresult = (event) => {{
            const transcript = event.results[0][0].transcript;
            statusEl.innerText = "Heard: " + transcript;
            const url = new URL(window.parent.location);
            url.searchParams.set("{key}", transcript);
            window.parent.history.replaceState({{}}, "", url);
            window.parent.location.reload();
        }};

        recognition.onerror = (event) => {{
            statusEl.innerText = "Error: " + event.error;
        }};

        recognition.onend = () => {{
            if (statusEl.innerText === "Listening...") {{
                statusEl.innerText = "No speech detected.";
            }}
        }};
    }}
    </script>
    """
    components.html(component_html, height=50)


def speak_text(text: str, key: str):
    """
    Uses the browser's built-in Text-to-Speech (SpeechSynthesis API) to read
    text aloud. No API key, no cost - runs entirely client-side.
    Stores the synthesis controller on `window` so a separate stop button
    (see stop_speaking_button) can cancel it mid-sentence.
    """
    import streamlit.components.v1 as components
    import json

    safe_text = json.dumps(text)  # safely escape quotes/newlines for JS

    component_html = f"""
    <script>
    (function() {{
        window.speechSynthesis.cancel();  // stop any previous speech first
        const utterance = new SpeechSynthesisUtterance({safe_text});
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.__codelens_speaking = true;
        utterance.onend = () => {{ window.__codelens_speaking = false; }};
        utterance.onerror = () => {{ window.__codelens_speaking = false; }};
        window.speechSynthesis.speak(utterance);
    }})();
    </script>
    """
    components.html(component_html, height=0)


def stop_speaking_button(key: str = "stop_speak"):
    """
    Renders a button that immediately cancels any in-progress browser
    text-to-speech playback (from speak_text above).
    """
    import streamlit.components.v1 as components

    component_html = f"""
    <button id="stop-btn-{key}" onclick="stopSpeaking_{key}()"
        style="background:#1C242E;border:1px solid #F85149;color:#F85149;
               border-radius:6px;padding:8px 16px;cursor:pointer;
               font-family:'JetBrains Mono',monospace;font-size:13px;">
        ⏹ Stop speaking
    </button>
    <script>
    function stopSpeaking_{key}() {{
        window.parent.window.speechSynthesis.cancel();
    }}
    </script>
    """
    components.html(component_html, height=46)


def voice_chat_widget(key: str = "voice_assistant"):
    """
    A self-contained mic button + status display for the general voice
    assistant tab. Returns the transcribed question via st.query_params[key]
    once captured.
    """
    import streamlit.components.v1 as components

    component_html = f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:10px;padding:24px 0;">
        <button id="big-mic-{key}" onclick="startBigListening_{key}()"
            style="background:#1C242E;border:2px solid #4FD1C5;color:#4FD1C5;
                   border-radius:50%;width:84px;height:84px;cursor:pointer;
                   font-size:32px;display:flex;align-items:center;justify-content:center;
                   transition:transform 0.15s ease, box-shadow 0.2s ease;">
            🎤
        </button>
        <span id="big-mic-status-{key}" style="font-family:'JetBrains Mono',monospace;
              font-size:13px;color:#8B95A1;text-align:center;">
            Tap to ask a question
        </span>
    </div>
    <script>
    function startBigListening_{key}() {{
        const statusEl = document.getElementById("big-mic-status-{key}");
        const btnEl = document.getElementById("big-mic-{key}");
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            statusEl.innerText = "Speech recognition not supported. Try Chrome or Edge.";
            return;
        }}
        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        btnEl.style.boxShadow = "0 0 0 8px rgba(79,209,197,0.2)";
        statusEl.innerText = "Listening...";
        recognition.start();

        recognition.onresult = (event) => {{
            const transcript = event.results[0][0].transcript;
            statusEl.innerText = "Heard: " + transcript;
            const url = new URL(window.parent.location);
            url.searchParams.set("{key}", transcript);
            window.parent.history.replaceState({{}}, "", url);
            window.parent.location.reload();
        }};

        recognition.onerror = (event) => {{
            statusEl.innerText = "Error: " + event.error;
            btnEl.style.boxShadow = "none";
        }};

        recognition.onend = () => {{
            btnEl.style.boxShadow = "none";
        }};
    }}
    </script>
    """
    components.html(component_html, height=160)