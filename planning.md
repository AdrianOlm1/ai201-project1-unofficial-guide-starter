# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

I choose to focus on a guide for helping students at UCSC choose a college to be in. This is hard to find through official channels because the only information given is the description of the school and what they stand for but most of the known information is word of mouth around skill and what these colleges are actually like.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | City on a Hill Press — "Eleven Things to Know Going Into Your First Year" | Student-newspaper listicle of survival tips for incoming UCSC students (study spots, dining, textbooks, campus exploration). | https://cityonahillpress.com/2014/07/21/eleven-things-to-know-going-into-your-first-year/ |
| 2 | City on a Hill Press — "A Guide to UCSC Housing" | Student-written walkthrough of the on-campus and off-campus housing process, including rental resources and timelines. | https://cityonahillpress.com/2026/03/01/a-guide-to-ucsc-housing/ |
| 3 | City on a Hill Press — "A Perfect Ten: UCSC's Residential Colleges" | Overview of all 10 residential colleges with vibe, location, and theme — long-form, paragraph-per-college structure. | https://cityonahillpress.com/2022/09/18/a-perfect-ten-ucscs-residential-colleges/ |
| 4 | City on a Hill Press — "A Guide to Taking the Bus for the Transit-Savvy" | Current student guide to Metro routes, Loop bus, and how to actually get around campus. | https://cityonahillpress.com/2023/09/27/a-guide-to-taking-the-bus-for-the-transit-savvy/ |
| 5 | City on a Hill Press — "A Simple Guide to Buses on Campus" (2008) | Older transit guide; useful as a stale-info contrast case for evaluating how the system handles outdated content. | https://cityonahillpress.com/2008/10/23/a-simple-guide-to-buses-on-campus/ |
| 6 | CollegeVine — "UCSC colleges ranked?" | Q&A response with subjective ranking and pros/cons of each residential college; short, opinionated. | https://www.collegevine.com/faq/31271/ucsc-colleges-ranked |
| 7 | CollegeVine — "What's Campus Life Like in UC Santa Cruz Dorms?" | Q&A on dorm/residential-life experience from a student perspective. (Swapped in for a Quora thread that blocked all scrapers.) | https://www.collegevine.com/faq/124138/what-s-campus-life-like-in-uc-santa-cruz-dorms |
| 8 | Niche — UC Santa Cruz Reviews | Aggregated short student reviews of UCSC overall — mix of positive and negative, very review-shaped. | https://www.niche.com/colleges/university-of-california-santa-cruz/reviews/ |
| 9 | Niche — UC Santa Cruz Campus Life | Student opinions specifically on dining, safety, social life, party scene — sectioned by topic. | https://www.niche.com/colleges/university-of-california-santa-cruz/campus-life/ |
| 10 | GoodTimes Santa Cruz — "The Best Places to Eat on the UCSC Campus" | Local publication's ranked dining listicle covering dining halls and campus cafes. | https://www.goodtimes.sc/best-places-to-eat-ucsc-university-of-california-santa-cruz-dining/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 700 characters

**Overlap:** 100 characters

**Reasoning:**
I'm using a recursive character splitter so chunks break at paragraph or sentence boundaries when possible instead of mid-word. My sources are a mix — long-form student newspaper articles, short reviews, and Q&A answers — so I needed something that handles all three. 700 characters fits about one paragraph or a couple of short reviews per chunk, which keeps each chunk on one topic. 100 characters of overlap keeps a sentence of context across chunk boundaries so I don't lose the start of a thought in the long articles. Bigger chunks would mix multiple topics together. Smaller ones would cut paragraphs in half.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2

**Top-k:**
5

**Production tradeoff reflection:**
if cost wasnt an issue I owuld try openAI's text-embedding-3-small because they have much better context limits and handle a broader set of words but the tradeoff should be fine
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which UCSC dining hall do students recommend most? | Cowell/Stevenson and Rachel Carson/Oakes are mentioned most often. |
| 2 | Do UCSC students have to pay for Santa Cruz Metro buses? | No — free with a valid student ID and a quarter sticker. |
| 3 | Where on campus is a good quiet place to study? | McHenry Library. |
| 4 | How can I save money on textbooks at UCSC? | Buy used through Amazon, friends, or local bookstores like Bookshop Santa Cruz or the Literary Guillotine. |
| 5 | Which residential college is known for being smaller and community-focused? | Oakes College. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Some sources are old and might feed bad information like different bus routes

2. Because I am using the free embedded model, specific words like (Crown, Oakes, Slug, Loop) might get be vectorized incorrectly

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

     10 articles -> [Ingestion] ------> Chunking ---------------- > [Embedding](all-miniLM)
                    (Strip HTML)        Recursive splitter                 |
                    (Beautiful Soup)                                       |
     ↓. ____________________________________________________________________

     [Vector Store] -> [Retrieval] ------------> [Generation]
     ChromaDB.         top 5 nearest chunks       LLM (Groq — Llama 3)
                         cosine similarity

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I'll give claude my chunking stategy( 700 chars, 100 overlap, recursive spliter, with beautifu soup) and Ill test it on one documents and check if the couple chunks are coherent paragaphs from the text.

**Milestone 4 — Embedding and retrieval:**
Ill give claude my retrival approach (all-minilm-l6-v2, chromadb, write(query, k=5)) and ask it answer one of my evaluation questions and Ill see which 5 chunks it uses and see if the chunks are relevant

**Milestone 5 — Generation and interface:**
 I'll give Claude the retrieval function and a system prompt that says "only answer using the provided context, and if the answer isn't in the context, say you don't know." I'll run all 5 evaluation questions through the full pipeline and grade each one by hand against my expected answers.