"""Milestone 3 — Chunking.

Reads every cleaned .txt in documents/ and splits it into ~700-character
chunks with ~100 characters of overlap, using a *recursive character splitter*.

Recursive splitter (the strategy from planning.md):
    Try to break on the biggest natural boundary first — a blank line between
    paragraphs ("\\n\\n") — then a single newline, then a sentence break (". "),
    then a space, and only as a last resort a hard character cut. This keeps
    each chunk on one topic instead of slicing a sentence in half.

Output:
    chunks.json — a list of {id, source, title, chunk_index, text, n_chars}
    that Milestone 4 (embedding) will read.

Run:  python chunk.py
"""

import json
import statistics
from pathlib import Path

from sources import SOURCES

DOCS_DIR = Path(__file__).parent / "documents"
OUT_PATH = Path(__file__).parent / "chunks.json"

CHUNK_SIZE = 700        # characters
CHUNK_OVERLAP = 100     # characters carried from the end of one chunk into the next
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]  # tried in order, biggest boundary first


# ----------------------------------------------------------------------------- #
# Recursive character splitter
# ----------------------------------------------------------------------------- #
def _split_on(text: str, separator: str) -> list[str]:
    """Split text on a separator (or into characters if separator is empty),
    dropping empty pieces."""
    pieces = list(text) if separator == "" else text.split(separator)
    return [p for p in pieces if p != ""]


def _merge(splits: list[str], separator: str) -> list[str]:
    """Greedily glue small pieces back together up to CHUNK_SIZE, carrying
    CHUNK_OVERLAP characters of tail context into the next chunk."""
    sep_len = len(separator)
    chunks: list[str] = []
    current: list[str] = []
    total = 0

    for piece in splits:
        added_len = len(piece) + (sep_len if current else 0)
        # If this piece would overflow the current chunk, close the chunk first.
        if total + added_len > CHUNK_SIZE and current:
            chunk = separator.join(current).strip()
            if chunk:
                chunks.append(chunk)
            # Slide the window: drop pieces from the front until the leftover
            # tail is within the overlap budget (this leftover becomes the
            # start of the next chunk, giving us continuity).
            while current and (
                total > CHUNK_OVERLAP
                or total + len(piece) + (sep_len if current else 0) > CHUNK_SIZE
            ):
                total -= len(current[0]) + (sep_len if len(current) > 1 else 0)
                current.pop(0)
        current.append(piece)
        total += len(piece) + (sep_len if len(current) > 1 else 0)

    chunk = separator.join(current).strip()
    if chunk:
        chunks.append(chunk)
    return chunks


def reattach_headings(pieces: list[str]) -> list[str]:
    """Glue short heading-only pieces onto the following chunk.

    When a section heading (e.g. "Stevenson College: Founded in 1966") is
    followed by a description longer than CHUNK_SIZE, the splitter flushes the
    heading on its own before recursing into the long paragraph — orphaning a
    ~30-char chunk that carries the college name but none of its content, while
    the description chunk carries content but not the name. This re-joins them
    so the name and its description stay retrievable together.
    """
    out: list[str] = []
    held: str | None = None  # heading(s) waiting to attach to the next chunk

    def is_heading(p: str) -> bool:
        p = p.strip()
        # Short, and doesn't end like a finished sentence.
        return 0 < len(p) < 60 and p[-1] not in ".!?\"')"

    for piece in pieces:
        if is_heading(piece):
            held = piece if held is None else f"{held}\n\n{piece}"
            continue
        if held is not None:
            out.append(f"{held}\n\n{piece}")
            held = None
        else:
            out.append(piece)
    if held is not None:                      # trailing heading with no body
        if out:
            out[-1] = f"{out[-1]}\n\n{held}"
        else:
            out.append(held)
    return out


def recursive_split(text: str, separators: list[str] = SEPARATORS) -> list[str]:
    """Split text into <= ~CHUNK_SIZE chunks, preferring natural boundaries."""
    # Pick the first separator that actually occurs in the text.
    separator = separators[-1]
    remaining = []
    for i, sep in enumerate(separators):
        if sep == "":
            separator = sep
            break
        if sep in text:
            separator = sep
            remaining = separators[i + 1:]
            break

    final: list[str] = []
    good: list[str] = []
    for piece in _split_on(text, separator):
        if len(piece) < CHUNK_SIZE:
            good.append(piece)
        else:
            # Flush the small pieces we've accumulated, then recurse on the
            # oversized piece using the next-smaller separator.
            if good:
                final.extend(_merge(good, separator))
                good = []
            if remaining:
                final.extend(recursive_split(piece, remaining))
            else:
                final.append(piece)  # nothing left to split on
    if good:
        final.extend(_merge(good, separator))
    return final


# ----------------------------------------------------------------------------- #
# Drive the corpus and report stats
# ----------------------------------------------------------------------------- #
def main() -> None:
    title_by_file = {s["filename"]: s["title"] for s in SOURCES}
    all_chunks = []
    per_source = {}

    for path in sorted(DOCS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        pieces = reattach_headings(recursive_split(text))
        per_source[path.name] = len(pieces)
        for i, piece in enumerate(pieces):
            all_chunks.append({
                "id": f"{path.stem}__{i}",
                "source": path.name,
                "title": title_by_file.get(path.name, path.name),
                "chunk_index": i,
                "text": piece,
                "n_chars": len(piece),
            })

    OUT_PATH.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    # ---- Report ----------------------------------------------------------- #
    lengths = [c["n_chars"] for c in all_chunks]
    print(f"Total chunks: {len(all_chunks)}\n")
    print("Chunks per source:")
    for name in sorted(per_source):
        print(f"  {name:<40} {per_source[name]:>3}")
    print("\nChunk length (characters):")
    print(f"  min    {min(lengths)}")
    print(f"  max    {max(lengths)}")
    print(f"  mean   {statistics.mean(lengths):.0f}")
    print(f"  median {statistics.median(lengths):.0f}")
    tiny = sum(1 for n in lengths if n < 100)
    print(f"  chunks under 100 chars: {tiny}")
    print(f"\nWrote {OUT_PATH.name}")


if __name__ == "__main__":
    main()
