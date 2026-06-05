# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Unofficial guide to student life at UC Santa Cruz. The system covers residential colleges, getting around campus on the Metro and Loop buses, housing, and first-year stuff like dining halls and study spots. Official UCSC pages list facts (each college's theme, bus schedules) but don't tell you which college a student would actually like, which dining hall is worth the walk, or what longtime students wish they'd known. That kind of knowledge lives in student newspaper articles, review sites, and Q&A threads.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | City on a Hill Press — "Eleven Things to Know Going Into Your First Year" | Student newspaper listicle | https://cityonahillpress.com/2014/07/21/eleven-things-to-know-going-into-your-first-year/ |
| 2 | City on a Hill Press — "A Guide to UCSC Housing" | Student newspaper long-form guide | https://cityonahillpress.com/2026/03/01/a-guide-to-ucsc-housing/ |
| 3 | City on a Hill Press — "A Perfect Ten: UCSC's Residential Colleges" | Student newspaper overview article | https://cityonahillpress.com/2022/09/18/a-perfect-ten-ucscs-residential-colleges/ |
| 4 | City on a Hill Press — "A Guide to Taking the Bus for the Transit-Savvy" | Student newspaper transit guide | https://cityonahillpress.com/2023/09/27/a-guide-to-taking-the-bus-for-the-transit-savvy/ |
| 5 | City on a Hill Press — "A Simple Guide to Buses on Campus" (2008) | Older student newspaper guide (outdated-info contrast) | https://cityonahillpress.com/2008/10/23/a-simple-guide-to-buses-on-campus/ |
| 6 | CollegeVine — "UCSC colleges ranked?" | Q&A forum answer | https://www.collegevine.com/faq/31271/ucsc-colleges-ranked |
| 7 | CollegeVine — "What's Campus Life Like in UC Santa Cruz Dorms?" | Q&A forum thread (dorm/residential life) | https://www.collegevine.com/faq/124138/what-s-campus-life-like-in-uc-santa-cruz-dorms |
| 8 | Niche — UC Santa Cruz Reviews | Aggregated short student reviews | https://www.niche.com/colleges/university-of-california-santa-cruz/reviews/ |
| 9 | Niche — UC Santa Cruz Campus Life | Sectioned student opinions on dining/safety/social | https://www.niche.com/colleges/university-of-california-santa-cruz/campus-life/ |
| 10 | GoodTimes Santa Cruz — "The Best Places to Eat on the UCSC Campus" | Local publication dining listicle | https://www.goodtimes.sc/best-places-to-eat-ucsc-university-of-california-santa-cruz-dining/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 700 characters

**Overlap:** 100 characters

**Why these choices fit your documents:** I used a recursive character splitter so chunks break at paragraph or sentence boundaries when possible, not mid-word. My sources are a mix of long-form student newspaper articles, short reviews, and Q&A answers. 700 characters fits about one paragraph or a couple of short reviews per chunk, which keeps each chunk on one topic. 100 characters of overlap keeps a sentence of context across chunk boundaries so I don't lose the start of a thought in the long articles. Bigger chunks would mix multiple topics together; smaller ones would cut paragraphs in half. Preprocessing: stripped HTML/scripts/nav/footer with BeautifulSoup, collapsed whitespace but preserved `\n\n` paragraph breaks, removed bylines and "share this article" boilerplate.

**Final chunk count:** 104 chunks across the 10 documents (mean ~515 chars, median ~550, range 172–725, none under 100 chars).

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2`, run through ChromaDB. It's small, free, runs locally without an API key, and is fast for ~100 chunks. I originally planned to load it via the `sentence-transformers` package, but that requires PyTorch, which has no install candidate for Python 3.13 on Intel macOS — so I used the same model through ChromaDB's `onnxruntime`-based embedding function instead (same weights, same embeddings, no torch). Query text is embedded with the exact same function so the vectors are comparable. Retrieval uses cosine distance, top-k = 5.

**Production tradeoff reflection:** If cost wasn't a concern I'd try OpenAI's `text-embedding-3-small` or `3-large`. They have longer context limits and probably handle UCSC-specific words (Crown, Oakes, campus slang) better since they're trained on more data. The tradeoffs are paying per query and relying on a hosted API. My sources are all English, so multilingual support didn't matter here.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**Generation model:** Groq `llama-3.3-70b-versatile`

**System prompt grounding instruction** (the actual system message in `generate.py`):

```
You are the Unofficial Guide to UC Santa Cruz (UCSC), answering questions
for students using firsthand student writing.
Follow these rules strictly:
1. Answer ONLY using the numbered context sources provided. Do not use any
   outside knowledge.
2. If the answer is not contained in the context, reply exactly:
   "I don't know based on the available sources."
3. After each claim, cite the source(s) it came from in brackets, e.g. [Source 2].
4. Be concise and specific. Do not invent dining halls, bus routes, prices,
   or college names that are not in the context.
```

The user message then supplies the retrieved context as numbered blocks
(`[Source 1] (from: <title>)\n<chunk text>`) followed by `Question: <q>`.

I keep the model grounded three ways: the prompt tells it to only use the sources and to reply "I don't know based on the available sources" if the answer isn't there, the context is split into numbered `[Source N]` blocks so every fact has a source attached, and I set the temperature to 0.1 so it stays close to the text. This worked on the Oakes question (see Failure Case Analysis) — that answer wasn't retrieved, so the model said "I don't know" instead of making up a college.

**How source attribution is surfaced:** Each `[Source N]` maps back to the chunk it came from and its original document. The model cites `[Source N]` after each claim, and `generate.py` prints a "Sources cited" list with each title and URL.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which UCSC dining hall do students recommend most? | Cowell/Stevenson and Rachel Carson/Oakes are mentioned most often. | "The Rachel Carson/Oakes Dining Hall is recommended the most… first place, newest/grandest." [GoodTimes] | Partially relevant (dining doc retrieved, but at rank 4; top chunk was off-topic) | Accurate but partial (names RC/Oakes, the #1 hall; doesn't mention Cowell/Stevenson) |
| 2 | Do UCSC students have to pay for Santa Cruz Metro buses? | No — free with a valid student ID and a quarter sticker. | "No, students do not pay if they have a valid university ID." [CoHP bus guide 2023] | Relevant (exact chunk at rank 1, similarity 0.80) | Accurate |
| 3 | Where on campus is a good quiet place to study? | McHenry Library. | "The higher floors of McHenry Library, specifically the fourth floor." [CoHP Eleven Things] | Relevant (rank 1) | Accurate |
| 4 | How can I save money on textbooks at UCSC? | Buy used through Amazon, friends, or local bookstores like Bookshop Santa Cruz or the Literary Guillotine. | "Buy from friends, Amazon, or local bookstores like the Literary Guillotine and Bookshop Santa Cruz." [CoHP Eleven Things] | Relevant (rank 1) | Accurate |
| 5 | Which residential college is known for being smaller and community-focused? | Oakes College. | "I don't know based on the available sources." | Off-target (the Oakes chunk never entered the top 5 — see Failure Case Analysis) | No answer, but a correct refusal — the answer wasn't retrieved, so it didn't guess |

**Summary:** 4 of 5 answered correctly with citations. The Oakes question failed at retrieval, and because of the grounding the model said "I don't know" instead of guessing.

**Retrieval quality:** Partially relevant
**Response accuracy:** Accurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "Which residential college is known for being smaller and community-focused?" (expected answer: **Oakes College**).

**What the system returned:** "I don't know based on the available sources." The Oakes answer never showed up in the top 5 retrieved chunks, even though the sentence *"Oakes College … a smaller, tight-knit atmosphere"* is in my documents.

**Root cause (tied to a specific pipeline stage):** The **chunking stage**. The colleges-ranked doc is a numbered list, and each college is only about 250 characters. My chunker aims for 700 characters, so it put two colleges in one chunk — Kresge and Oakes ended up together. That chunk gets one embedding that mixes both colleges, so when I ask specifically about Oakes the match is weak and it gets buried.

**What you would change to fix it:** Split list-style documents by list item instead of by character count, so each college becomes its own chunk with its own embedding. A simpler fix would be a smaller chunk size for that one document.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the chunking strategy in planning.md first gave me exact numbers to build from — 700 characters, 100 overlap, recursive splitter. When it was time to write the code I wasn't guessing, I just implemented what I'd already decided. It also made the failure case easier to explain, since I already knew why I picked that chunk size.

**One way your implementation diverged from the spec, and why:** I planned to load all-MiniLM-L6-v2 with the `sentence-transformers` package, but it needs PyTorch, which won't install on Python 3.13 on my Intel Mac. I used the same model through ChromaDB's ONNX embedding function instead, so the embeddings are the same but I didn't need torch.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* My two cleaned Niche files, which looked useless — just star ratings and dates, no actual review text.
- *What it produced:* It found that Niche puts each review in a `<span class="review__text">` instead of a `<p>` tag, which my scraper was skipping, and added a step to grab those spans.
- *What I changed or overrode:* I kept the fix but also had it filter out the leftover rating and timestamp lines, so the files ended up as real reviews instead of metadata.

**Instance 2**

- *What I gave the AI:* My chunk output to look over.
- *What it produced:* It noticed college headings like "Stevenson College: Founded in 1966" were being split into their own tiny chunks, separated from the description.
- *What I changed or overrode:* I had it add a step that reattaches a short heading to the chunk after it, so the college name stays with its description.
