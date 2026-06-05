"""Unofficial UCSC Guide — Streamlit dashboard.

A single interface for the whole RAG pipeline:
  • Pipeline panel  — run ingest / chunk / embed and watch their output
  • Ask             — ask a question, get a grounded answer + cited sources
  • Browse chunks   — read the 104 chunks, grouped by source
  • Documents       — read the cleaned source text for each of the 10 docs

Run it:
    .venv/bin/python -m streamlit run app.py
"""

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

from sources import SOURCES

ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "documents"
CHUNKS_PATH = ROOT / "chunks.json"
DB_PATH = ROOT / "chroma_db"

SOURCE_INFO = {s["filename"]: s for s in SOURCES}

st.set_page_config(page_title="Unofficial UCSC Guide", page_icon="🐌", layout="wide")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def run_script(filename: str):
    """Run a pipeline script with the same Python and capture its output."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / filename)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def n_documents() -> int:
    return len(list(DOCS_DIR.glob("*.txt")))


@st.cache_data(show_spinner=False)
def load_chunks(_mtime: float):
    """Load chunks.json (cached; busts when the file's mtime changes)."""
    if CHUNKS_PATH.exists():
        return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return []


def get_chunks():
    mtime = CHUNKS_PATH.stat().st_mtime if CHUNKS_PATH.exists() else 0.0
    return load_chunks(mtime)


def vector_count() -> int:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(DB_PATH))
        return client.get_collection("ucsc_guide").count()
    except Exception:
        return 0


def reset_retrieval_cache():
    """After re-embedding, drop the cached collection handle in retrieve.py so
    the next question opens the freshly rebuilt vector store."""
    try:
        import retrieve
        retrieve._collection = None
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Sidebar — pipeline status + controls
# --------------------------------------------------------------------------- #
st.sidebar.title("🐌 Pipeline")

n_docs, n_chunks, n_vecs = n_documents(), len(get_chunks()), vector_count()
st.sidebar.metric("Documents", n_docs)
st.sidebar.metric("Chunks", n_chunks)
st.sidebar.metric("Vectors in store", n_vecs)

st.sidebar.caption("Run the stages in order. Each shows its console output below.")

steps = [
    ("1 · Ingest", "ingest.py", "Download + clean the 10 source pages → documents/"),
    ("2 · Chunk", "chunk.py", "Split documents into ~700-char chunks → chunks.json"),
    ("3 · Embed", "embed.py", "Embed chunks + build the ChromaDB vector store"),
]
for label, script, help_text in steps:
    if st.sidebar.button(label, help=help_text, use_container_width=True):
        with st.spinner(f"Running {script} …"):
            code, output = run_script(script)
        if script == "embed.py":
            reset_retrieval_cache()
        (st.sidebar.success if code == 0 else st.sidebar.error)(
            f"{script} {'finished' if code == 0 else 'failed'}"
        )
        st.session_state["last_output"] = (script, output)
        st.rerun()

if "last_output" in st.session_state:
    script, output = st.session_state["last_output"]
    with st.sidebar.expander(f"Output of {script}", expanded=False):
        st.code(output or "(no output)", language="text")


# --------------------------------------------------------------------------- #
# Main — tabs
# --------------------------------------------------------------------------- #
st.title("The Unofficial Guide to UC Santa Cruz")
st.caption("Ask about residential colleges, dining, buses, housing, and surviving "
           "first year — answered only from real student writing.")

tab_ask, tab_chunks, tab_docs = st.tabs(["💬 Ask", "🔎 Browse chunks", "📄 Documents"])

# ---- Ask tab ----------------------------------------------------------------#
with tab_ask:
    if n_vecs == 0:
        st.warning("The vector store is empty. Run **1 · Ingest → 2 · Chunk → "
                   "3 · Embed** from the sidebar first.")
    EXAMPLES = [
        "Do UCSC students have to pay for the Metro bus?",
        "Where is a good quiet place to study?",
        "How can I save money on textbooks?",
        "Which dining hall do students like most?",
    ]
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, use_container_width=True):
            st.session_state["query"] = ex

    query = st.text_input(
        "Your question", value=st.session_state.get("query", ""),
        placeholder="e.g. What's the housing situation like after first year?",
    )
    ask = st.button("Ask", type="primary", disabled=(n_vecs == 0))

    if ask and query.strip():
        try:
            from generate import answer
            with st.spinner("Retrieving + generating …"):
                result = answer(query.strip())
            st.markdown("### Answer")
            st.write(result["text"])

            if result["cited"]:
                st.markdown("### Sources cited")
                for n in sorted(result["cited"]):
                    if 1 <= n <= len(result["hits"]):
                        h = result["hits"][n - 1]
                        info = SOURCE_INFO.get(h["source"], {})
                        url = info.get("url", "")
                        st.markdown(f"- **[Source {n}]** {h['title']}"
                                    + (f" — [link]({url})" if url else ""))

            with st.expander("Show the retrieved chunks (what the model saw)"):
                for i, h in enumerate(result["hits"], 1):
                    st.markdown(f"**[Source {i}]** `{h['source']}` "
                                f"· similarity {h['similarity']:.3f}")
                    st.write(h["text"])
                    st.divider()
        except SystemExit as e:
            st.error(str(e))
        except Exception as e:  # noqa: BLE001
            st.error(f"Something went wrong: {e}")

# ---- Browse chunks tab ------------------------------------------------------#
with tab_chunks:
    chunks = get_chunks()
    if not chunks:
        st.info("No chunks yet — run **2 · Chunk** from the sidebar.")
    else:
        st.write(f"**{len(chunks)} chunks** across {n_docs} documents.")
        by_source = sorted({c["source"] for c in chunks})
        picked = st.selectbox("Filter by source", ["(all)"] + by_source)
        shown = [c for c in chunks if picked == "(all)" or c["source"] == picked]
        st.caption(f"Showing {len(shown)} chunks.")
        for c in shown:
            with st.expander(f"{c['id']}  ·  {c['n_chars']} chars"):
                st.write(c["text"])

# ---- Documents tab ----------------------------------------------------------#
with tab_docs:
    files = sorted(DOCS_DIR.glob("*.txt"))
    if not files:
        st.info("No documents yet — run **1 · Ingest** from the sidebar.")
    else:
        names = [f.name for f in files]
        picked = st.selectbox("Document", names)
        info = SOURCE_INFO.get(picked, {})
        if info.get("title"):
            st.markdown(f"**{info['title']}**")
        if info.get("url"):
            st.markdown(f"[Original source]({info['url']})")
        text = (DOCS_DIR / picked).read_text(encoding="utf-8")
        st.caption(f"{len(text)} characters")
        st.text_area("Cleaned text", text, height=500)
