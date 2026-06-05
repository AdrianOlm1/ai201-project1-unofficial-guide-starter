"""Browse chunks.json in a readable way.

Examples:
    python view_chunks.py                  # summary: count + length per source
    python view_chunks.py --all            # print every chunk
    python view_chunks.py 08               # only chunks whose source contains "08"
    python view_chunks.py niche --full     # niche chunks, full text (not truncated)
    python view_chunks.py --n 5            # first 5 chunks of each match
"""

import json
import sys
from pathlib import Path

CHUNKS = Path(__file__).parent / "chunks.json"


def main() -> None:
    args = sys.argv[1:]
    show_all = "--all" in args
    full = "--full" in args
    limit = None
    skip_next = False
    filters = []
    for i, a in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if a == "--n":
            limit = int(args[i + 1])
            skip_next = True
        elif a.startswith("--"):
            continue
        else:
            filters.append(a)  # a source filter, e.g. "08" or "niche"

    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))

    # --- summary mode (no filter, no --all) ------------------------------- #
    if not filters and not show_all:
        per = {}
        for c in chunks:
            per[c["source"]] = per.get(c["source"], 0) + 1
        print(f"{len(chunks)} chunks total\n")
        for name in sorted(per):
            print(f"  {name:<40} {per[name]:>3} chunks")
        print('\nTip: `python view_chunks.py 08` to read one source, '
              'or `--all` to read everything.')
        return

    # --- read mode -------------------------------------------------------- #
    def matches(source: str, f: str) -> bool:
        # A numeric filter ("08"/"8") matches the filename's leading number,
        # so "08" does NOT accidentally match "...2008...". A word filter
        # ("niche") is a plain substring match.
        if f.isdigit():
            return source.split("_", 1)[0] == f.zfill(2)
        return f.lower() in source.lower()

    shown = 0
    for c in chunks:
        if filters and not any(matches(c["source"], f) for f in filters):
            continue
        if limit is not None and shown >= limit:
            break
        text = c["text"] if full else (c["text"][:300] + ("…" if len(c["text"]) > 300 else ""))
        print("─" * 78)
        print(f"{c['id']}   ({c['n_chars']} chars)   [{c['source']}]")
        print("─" * 78)
        print(text)
        print()
        shown += 1
    print(f"({shown} chunks shown)")


if __name__ == "__main__":
    main()
