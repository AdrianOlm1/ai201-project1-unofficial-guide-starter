"""Milestone 5 — Grounded Generation.

Ties the whole pipeline together: take a question, retrieve the top-k chunks
(retrieve.py), format them as numbered sources, and ask a Groq LLM to answer
USING ONLY those sources. The model is instructed to cite each claim and to
refuse ("I don't know …") when the answer isn't in the retrieved context — this
is what keeps the system grounded instead of hallucinating.

Setup:
    Put your key in a .env file:  GROQ_API_KEY=gsk_...
    (Get a free key at https://console.groq.com)

Use as a library:
    from generate import answer
    result = answer("Do students pay for the bus?")
    print(result["text"])

Command line:
    python generate.py "Where can I study quietly?"   # one question
    python generate.py                                 # interactive loop
    python generate.py --eval                          # run the 5 eval questions
"""

import os
import sys
import re

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve, EVAL_QUESTIONS
from sources import SOURCES

load_dotenv()

# Groq model. Override with GROQ_MODEL in .env if this name is ever retired.
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TOP_K = 5

# filename -> {url, title}, so we can show real links for each cited source.
SOURCE_INFO = {s["filename"]: s for s in SOURCES}

SYSTEM_PROMPT = (
    "You are the Unofficial Guide to UC Santa Cruz (UCSC), answering questions "
    "for students using firsthand student writing.\n"
    "Follow these rules strictly:\n"
    "1. Answer ONLY using the numbered context sources provided. Do not use any "
    "outside knowledge.\n"
    "2. If the answer is not contained in the context, reply exactly: "
    "\"I don't know based on the available sources.\"\n"
    "3. After each claim, cite the source(s) it came from in brackets, e.g. "
    "[Source 2].\n"
    "4. Be concise and specific. Do not invent dining halls, bus routes, prices, "
    "or college names that are not in the context."
)


def _build_context(hits: list[dict]) -> str:
    """Format retrieved chunks as numbered, labeled source blocks."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[Source {i}] (from: {h['title']})\n{h['text']}")
    return "\n\n".join(blocks)


def answer(query: str, k: int = TOP_K) -> dict:
    """Retrieve, then generate a grounded answer.

    Returns {text, hits, cited} where `hits` is the list of retrieved chunks and
    `cited` is the set of source numbers the model actually referenced.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise SystemExit(
            "No GROQ_API_KEY found. Add it to a .env file:\n"
            "  GROQ_API_KEY=gsk_...   (free key at https://console.groq.com)"
        )

    hits = retrieve(query, k=k)
    context = _build_context(hits)

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,  # low → stay faithful to the sources
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    text = resp.choices[0].message.content.strip()
    cited = {int(n) for n in re.findall(r"\[Source (\d+)\]", text)}
    return {"text": text, "hits": hits, "cited": cited}


def _print_answer(query: str, result: dict) -> None:
    print("\n" + "=" * 80)
    print(f"Q: {query}")
    print("=" * 80)
    print(result["text"])
    # Show the real source for each [Source N] the model cited.
    if result["cited"]:
        print("\nSources cited:")
        for n in sorted(result["cited"]):
            if 1 <= n <= len(result["hits"]):
                h = result["hits"][n - 1]
                info = SOURCE_INFO.get(h["source"], {})
                print(f"  [Source {n}] {h['title']}")
                if info.get("url"):
                    print(f"             {info['url']}")
    print()


def main() -> None:
    args = sys.argv[1:]
    if args == ["--eval"]:
        for q in EVAL_QUESTIONS:
            _print_answer(q, answer(q))
    elif args:
        q = " ".join(args)
        _print_answer(q, answer(q))
    else:
        print("Unofficial UCSC Guide — ask a question (Ctrl-C or blank line to quit).")
        try:
            while True:
                q = input("\n> ").strip()
                if not q:
                    break
                _print_answer(q, answer(q))
        except (KeyboardInterrupt, EOFError):
            print()


if __name__ == "__main__":
    main()
