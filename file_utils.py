"""
File reading & chunking utilities for the AI Code Reviewer.

Why this exists: LLMs have a token limit per request. A small file (50-200 lines)
fits fine in one call. A large file (1000+ lines) needs to be split into chunks,
reviewed separately, then the results combined - otherwise you either get an error
or the model only "sees" part of the file and gives an incomplete review.
"""

import os

# Rough rule of thumb: 1 token ≈ 4 characters in English/code.
# Llama 3.3 70B on Groq supports a large context window, but we keep chunks
# conservative so review quality stays high (smaller chunks = more focused review).
MAX_CHARS_PER_CHUNK = 6000  # ~1500 tokens per chunk, leaves room for prompt + response


def detect_language(filename: str) -> str:
    """Guess the programming language from a file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".sql": "sql",
        ".rb": "ruby",
        ".cpp": "cpp",
        ".c": "c",
        ".rs": "rust",
    }
    _, ext = os.path.splitext(filename)
    return ext_map.get(ext.lower(), "text")


def chunk_code(code: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """
    Split code into chunks that fit comfortably in one LLM call.

    Splits on blank lines where possible (keeps functions/classes intact
    rather than cutting them in half mid-function), falling back to a hard
    split only if a single block is itself larger than max_chars.
    """
    if len(code) <= max_chars:
        return [code]

    blocks = code.split("\n\n")  # split on blank lines (common function/class separators)
    chunks = []
    current_chunk = ""

    for block in blocks:
        # If a single block alone exceeds the limit, hard-split it
        if len(block) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            for i in range(0, len(block), max_chars):
                chunks.append(block[i:i + max_chars])
            continue

        if len(current_chunk) + len(block) + 2 <= max_chars:
            current_chunk += (block + "\n\n")
        else:
            chunks.append(current_chunk)
            current_chunk = block + "\n\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def needs_chunking(code: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> bool:
    """Quick check used by the UI to warn the user / show a progress bar."""
    return len(code) > max_chars


if __name__ == "__main__":
    # Quick self-test
    sample = "def foo():\n    pass\n\n" * 500  # artificially large file
    print(f"Sample length: {len(sample)} chars")
    print(f"Needs chunking: {needs_chunking(sample)}")
    chunks = chunk_code(sample)
    print(f"Split into {len(chunks)} chunks")
    print(f"Detected language for 'app.py': {detect_language('app.py')}")
    print(f"Detected language for 'script.js': {detect_language('script.js')}")