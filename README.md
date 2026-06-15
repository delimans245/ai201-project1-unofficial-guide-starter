# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Off-campus housing and Berkeley student co-op housing for UC Berkeley students.

This guide is useful because the information students actually need is spread across campus rental services, city tenant resources, co-op housing pages, and apartment listings. It is hard to find through a single official channel because rent, room type, commute, safety, and scam-avoidance details are maintained separately and change over time.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | UC Berkeley Off-Campus Rental Services | Web page | https://och.berkeley.edu/ |
| 2 | Avoid Scams & Fraud | Web page | https://och.berkeley.edu/avoid-scams-and-fraud |
| 3 | Contact Cal Rentals | Web page | https://och.berkeley.edu/resources/article/5422-contact-calrentals |
| 4 | Berkeley Rent Board home page | Web page | https://rentboard.berkeleyca.gov/ |
| 5 | Berkeley Rent Board registration page | Web page | https://rentboard.berkeleyca.gov/rights-responsibilities/registration |
| 6 | Berkeley Student Cooperative home page | Web page | https://bsc.coop/ |
| 7 | BSC Our Houses & Apartments | Web page | https://bsc.coop/housing/our-houses-apartments |
| 8 | BSC Academic Year Rates | Web page | https://bsc.coop/housing/academic-year-rates |
| 9 | Apartment List Berkeley city page | Web page | https://www.apartmentlist.com/ca/berkeley |
| 10 | Apartment List Downtown Berkeley page | Web page | https://www.apartmentlist.com/ca/berkeley/neighborhoods/downtown-berkeley |
| 11 | Apartment List Southside page | Web page | https://www.apartmentlist.com/ca/berkeley/neighborhoods/southside |
| 12 | Apartment List West Berkeley page | Web page | https://www.apartmentlist.com/ca/berkeley/neighborhoods/west-berkeley |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
50 tokens

**Overlap:**
15 tokens

**Why these choices fit your documents:**
The source files are short plain-text versions of the web pages, so a smaller chunk window keeps each chunk centered on one fact block while still preserving enough overlap for continuity.

**Final chunk count:**
65

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
sentence-transformers/all-MiniLM-L6-v2

**Production tradeoff reflection:**
I chose a small local embedding model because this corpus is mostly short factual housing pages and I wanted the retrieval stack to stay fast, cheap, and easy to debug. If cost were no constraint, I would consider a larger or domain-tuned model with better handling of noisy web text, more language coverage, and stronger semantic recall, even if that increased latency.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The system prompt tells the model to answer only from the provided documents, to avoid outside knowledge, and to reply exactly with "I don't have enough information on that." when the context is insufficient. The query layer also uses a distance threshold before calling the LLM, so obviously weak retrievals short-circuit to the no-information response instead of guessing.

**How source attribution is surfaced in the response:**
Source attribution is added programmatically from the retrieved chunks, not left for the model to invent. The UI shows a separate "Retrieved from" field listing the document titles and URLs returned by retrieval, which keeps attribution consistent even when the answer text changes.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What does BSC say a room-and-board house costs per semester, and what is included? | $4,986 per semester for Fall 2026 / Spring 2027; food, utilities, cleaning supplies, furniture, and co-op-wide events are included. | The system returned the $4,986 semester price and the included items from BSC Academic Year Rates. | Relevant | Accurate |
| 2 | Which BSC house is substance-free and academically themed? | Cloyne Court. | The system returned Cloyne Court as the substance-free, academically themed house. | Relevant | Accurate |
| 3 | Name two scam red flags listed by UC Berkeley Off-Campus Rental Services. | Examples include below-market rent, requests to wire money, inability to meet in person, and dramatic landlord stories. | The system returned below-market rent and requests to wire money. | Relevant | Accurate |
| 4 | How does Apartment List describe Downtown Berkeley, and what drawback does it mention? | Urban/bustling/walkable; it warns about possible 2AM noise and limited parking during events. | The system returned urban, bustling, walkable and the 2AM noise / limited parking drawback. | Relevant | Accurate |
| 5 | What is the average rent for a 1-bedroom apartment in Berkeley according to Apartment List? | $2,665+ per month. | The system returned $2,665+ per month from the Berkeley city page. | Relevant | Accurate |

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

**Question that failed:**
How does Apartment List describe Downtown Berkeley, and what drawback does it mention?

**What the system returned:**
Before I added title-based reranking, the retrieval step returned a West Berkeley chunk first because the text shared similar words like "walkable" and "rental market." The final answer was still correct, but the top retrieved source was not the best match.

**Root cause (tied to a specific pipeline stage):**
The retrieval stage was over-relying on semantic similarity between neighborhood descriptions, and West Berkeley contained language that was too close to Downtown Berkeley. The chunk text itself was fine; the ranking needed a stronger source-title signal.

**What you would change to fix it:**
I removed the overlapping "walkable" phrasing from the West Berkeley source text and added a lightweight title-based reranker so exact neighborhood names like "Downtown Berkeley" outrank semantically similar but wrong neighborhoods.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The planning file kept the pipeline concrete by forcing me to name the source set, the chunking strategy, the vector store, and the grounding rule before I wrote any code. That made it easier to verify each stage separately instead of guessing my way through the implementation.

**One way your implementation diverged from the spec, and why:**
I had to diverge from the original scrape-first approach because the housing site blocked direct requests from the terminal. I switched to local plain-text source files and reduced the chunk size from the original 800-token plan to 50 tokens after the local corpus proved it needed more context-preserving splits.

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
- My planning.md chunking and documents sections, plus the requirement to build an ingestion pipeline.
- *What it produced:*
- A first-pass scraper/chunker structure that assumed live requests.
- *What I changed or overrode:*
- I replaced the live scrape with local plain-text source files after the site blocked requests, but kept the sentence-based chunking shape.

**Instance 2**

- *What I gave the AI:*
- My retrieval architecture, grounding requirement, and interface skeleton.
- *What it produced:*
- A ChromaDB + Groq wiring pattern with a basic query UI.
- *What I changed or overrode:*
- I made source attribution programmatic, added a no-information fallback, and added a title-aware reranker so neighborhood-specific queries preferred the right source.
