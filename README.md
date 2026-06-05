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

**Model used:** `all-MiniLM-L6-v2` (384-dim), run through ChromaDB's built-in ONNX embedding function. It's small, free, runs locally without an API key, and is fast for ~100 chunks. I originally planned to load it via the `sentence-transformers` package, but that requires PyTorch, which has no install candidate for Python 3.13 on Intel macOS — so I used the same model through ChromaDB's `onnxruntime`-based embedding function instead (same weights, same embeddings, no torch). Query text is embedded with the exact same function so the vectors are comparable. Retrieval uses cosine distance, top-k = 5.

**Production tradeoff reflection:** If cost wasn't a concern I'd try OpenAI's `text-embedding-3-small` or `3-large`. They have much longer context limits and probably handle UCSC-specific words (college names like Crown or Oakes, campus slang) better since they're trained on more data. The tradeoffs would be paying per query, adding API latency, and depending on a hosted service. For multilingual coverage I'd consider a model like `multilingual-e5-large`, but my sources are all English so that's not relevant here.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

```
You are answering questions about student life at UC Santa Cruz.
Use ONLY the context provided below to answer. Do not use outside knowledge.
If the context does not contain the answer, say "I don't know based on the available sources."
After each claim, cite the source it came from using the format [Source N], matching the labels in the context.

Context:
[Source 1] {chunk text from top-1 retrieved chunk}
[Source 2] {chunk text from top-2 retrieved chunk}
...
[Source 5] {chunk text from top-5 retrieved chunk}

Question: {user question}
```

The grounding is enforced two ways: the system prompt explicitly tells the model not to use outside knowledge and to say "I don't know" when the context is missing the answer, and the context is formatted as numbered `[Source N]` blocks so each chunk is labeled and citable.

**How source attribution is surfaced in the response:** Each chunk fed to the model carries a `[Source N]` label that maps to one of the original 10 documents (tracked in the vector store metadata). The model is instructed to cite `[Source N]` after each claim, and after the answer is generated the application appends the corresponding URLs to the response so the user can verify each cited claim against the original document.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which UCSC dining hall do students recommend most? | Cowell/Stevenson and Rachel Carson/Oakes are mentioned most often. | _(fill after running)_ | | |
| 2 | Do UCSC students have to pay for Santa Cruz Metro buses? | No — free with a valid student ID and a quarter sticker. | _(fill after running)_ | | |
| 3 | Where on campus is a good quiet place to study? | McHenry Library. | _(fill after running)_ | | |
| 4 | How can I save money on textbooks at UCSC? | Buy used through Amazon, friends, or local bookstores like Bookshop Santa Cruz or the Literary Guillotine. | _(fill after running)_ | | |
| 5 | Which residential college is known for being smaller and community-focused? | Oakes College. | _(fill after running)_ | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

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

**What the system returned:** The top-5 retrieved chunks were two chunks from the colleges-ranked FAQ (leading with College Nine and College Ten), two chunks from the dorm-life FAQ about general "community," and a Niche review mentioning "smaller communities." The chunk that actually answers the question — *"6. Oakes College … well-known for its supportive community … a smaller, tight-knit atmosphere"* — never appeared in the top 5, even though that exact sentence exists in the corpus. Pushing k up to 12 still did not surface it. Even when I queried the literal phrase "Oakes College smaller tight-knit community," the only chunk holding that answer came back leading with its Kresge text — because the Oakes sentence shares a single embedding with the Kresge item it was chunked together with.

**Root cause (tied to a specific pipeline stage):** The **chunking stage**. The colleges-ranked document is a numbered list where each college is a short (~250-character) item. My recursive splitter targets 700 characters, so it merged two list items into one chunk — chunk `06_collegevine_colleges_ranked__3` contains *both* Kresge (item 5) **and** Oakes (item 6). A chunk gets a single embedding vector, so that vector is an average of "Kresge" and "Oakes" content. When the query asks specifically about Oakes, the blended vector is a weak, diluted match, and the Oakes information is effectively buried — the embedding can't represent one college cleanly when the chunk is about two. This is a mixed-topic-chunk problem: a chunk size tuned for paragraph-style guides is too coarse for list-style documents where each line is its own topic.

**What you would change to fix it:** Chunk list-style documents by list item instead of by character count — split the colleges-ranked FAQ on its numbered-item boundaries (`1.`, `2.`, …) so each college becomes its own chunk with its own embedding. A lighter-weight alternative is to lower the chunk size for that document, or to prepend each item's subject (the college name) so the embedding is anchored to it. A more general fix would be hybrid retrieval: combine the vector search with a keyword match on "Oakes," which would pull the right item even when its embedding is diluted.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

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

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
