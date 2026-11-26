"""
Stage 6: ask accessibility questions (RAG).

Example:
    python ask.py "Do decorative images need alt text?"
"""

from __future__ import annotations

import sys

from a11y_helper.rag import ask


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python ask.py "your question"')
        return 1
    result = ask(" ".join(sys.argv[1:]))
    print(result["answer"])
    print("\nSources:")
    for i, s in enumerate(result["sources"], start=1):
        print(f"  [{i}] {s['title']} (score {s['score']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
