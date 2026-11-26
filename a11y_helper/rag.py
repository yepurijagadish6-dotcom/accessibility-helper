"""
Stage 6: RAG ("Retrieval-Augmented Generation") - "Ask WCAG".

You ask a question about accessibility. The tool:
  1. LOADS a small knowledge base (knowledge/wcag_notes.md)
  2. CHUNKS it into small passages (one per section, long ones split with overlap)
  3. RETRIEVES the passages most relevant to your question (TF-IDF + cosine similarity)
  4. GENERATES an answer with Claude, using ONLY those passages, and cites them

Why RAG? The model answers from trusted documents instead of from memory, which
reduces made-up answers and lets us show sources.

Retrieval here uses TF-IDF (word-based) so it runs offline with no extra
packages. A natural next step is to swap in vector embeddings and a vector
database; the rest of the pipeline stays the same.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_FILE = Path(__file__).resolve().parent.parent / "knowledge" / "wcag_notes.md"
DEFAULT_MODEL = os.environ.get("A11Y_MODEL", "claude-haiku-5-5")
STOPWORDS = set("""a an the and or of to in on for is are be with as by it this that from at
what how do does should can i my we you your our not no if when which who why""".split())


@dataclass
class Chunk:
    title: str
    text: str


# ---------- 1 + 2: load and chunk ----------

def load_chunks(path: Path = KNOWLEDGE_FILE, max_words: int = 120, overlap: int = 30) -> list[Chunk]:
    """Split the markdown file by '## ' headings; split long sections into overlapping windows."""
    content = path.read_text(encoding="utf-8")
    chunks: list[Chunk] = []
    for section in re.split(r"^## ", content, flags=re.MULTILINE)[1:]:
        title, _, body = section.partition("\n")
        words = body.split()
        if len(words) <= max_words:
            chunks.append(Chunk(title.strip(), " ".join(words)))
            continue
        step = max_words - overlap
        for start in range(0, len(words), step):
            chunks.append(Chunk(title.strip(), " ".join(words[start:start + max_words])))
            if start + max_words >= len(words):
                break
    return chunks


# ---------- 3: retrieve ----------

def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


class TfidfIndex:
    """A tiny search index: scores each chunk by how well its words match the question."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        docs = [tokenize(c.title + " " + c.text) for c in chunks]
        n = len(docs)
        doc_freq = Counter(word for doc in docs for word in set(doc))
        self.idf = {w: math.log((1 + n) / (1 + df)) + 1 for w, df in doc_freq.items()}
        self.vectors = [self._vector(doc) for doc in docs]

    def _vector(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        vec = {w: count * self.idf.get(w, 0.0) for w, count in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}

    def search(self, question: str, k: int = 3) -> list[tuple[Chunk, float]]:
        q = self._vector(tokenize(question))
        scored = [
            (chunk, sum(q.get(w, 0.0) * v for w, v in vec.items()))
            for chunk, vec in zip(self.chunks, self.vectors)
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [(c, s) for c, s in scored[:k] if s > 0]


# ---------- 4: generate ----------

def build_prompt(question: str, passages: list[Chunk]) -> str:
    context = "\n\n".join(f"[{i}] {p.title}\n{p.text}" for i, p in enumerate(passages, start=1))
    return (
        "You are an accessibility assistant for a university web team.\n"
        "Answer the question using ONLY the numbered passages below. "
        "Cite passages like [1] or [2]. If the passages do not contain the answer, "
        "say you don't know rather than guessing.\n\n"
        f"Passages:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


def ask(question: str, k: int = 3, model: str = DEFAULT_MODEL) -> dict:
    """Full RAG pipeline. Works without an API key (returns retrieved passages only)."""
    index = TfidfIndex(load_chunks())
    results = index.search(question, k=k)
    passages = [c for c, _ in results]
    sources = [{"title": c.title, "score": round(s, 3)} for c, s in results]

    if not passages:
        return {"answer": "I couldn't find anything relevant in the knowledge base.", "sources": [], "ai": False}

    if not os.environ.get("ANTHROPIC_API_KEY"):
        preview = "\n\n".join(f"- {p.title}: {p.text[:220]}..." for p in passages)
        return {"answer": "(No API key set, showing retrieved passages only)\n\n" + preview,
                "sources": sources, "ai": False}
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=model, max_tokens=800,
            messages=[{"role": "user", "content": build_prompt(question, passages)}],
        )
        answer = "".join(b.text for b in message.content if getattr(b, "type", "") == "text").strip()
        return {"answer": answer, "sources": sources, "ai": True}
    except Exception as exc:
        return {"answer": f"AI call failed ({exc}). Retrieved: " + ", ".join(p.title for p in passages),
                "sources": sources, "ai": False}
