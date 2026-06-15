# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Off-campus housing and Berkeley student co-op housing for UC Berkeley students.

This knowledge is valuable because rent, commute, room type, meal plans, and landlord scam warnings are scattered across campus services, city tenant rules, cooperative housing pages, and apartment listings. It is hard to find in one place because official sites focus on policies and listings, while the practical tradeoffs students care about are spread across multiple sources and change independently.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | UC Berkeley Off-Campus Rental Services | Campus hub for off-campus rentals, roommates, and support | https://och.berkeley.edu/ |
| 2 | Avoid Scams & Fraud | Scam red flags, reporting steps, and roommate safety advice | https://och.berkeley.edu/avoid-scams-and-fraud |
| 3 | Contact Cal Rentals | Contact info and office details for the campus rental office | https://och.berkeley.edu/resources/article/5422-contact-calrentals |
| 4 | Berkeley Rent Board home page | Tenant-rights news, resources, and city housing services | https://rentboard.berkeleyca.gov/ |
| 5 | Berkeley Rent Board registration page | Registration rules and unit registration guidance | https://rentboard.berkeleyca.gov/rights-responsibilities/registration |
| 6 | Berkeley Student Cooperative home page | Membership, mission, and housing system overview | https://bsc.coop/ |
| 7 | BSC Our Houses & Apartments | House-specific descriptions, eligibility, food, and workshift details | https://bsc.coop/housing/our-houses-apartments |
| 8 | BSC Academic Year Rates | Co-op costs, payment schedule, and what is included in rent | https://bsc.coop/housing/academic-year-rates |
| 9 | Apartment List Berkeley city page | Berkeley rent overview, FAQs, and neighborhood summaries | https://www.apartmentlist.com/ca/berkeley |
| 10 | Apartment List Downtown Berkeley page | Downtown listings, price bands, and walkability/noise context | https://www.apartmentlist.com/ca/berkeley/neighborhoods/downtown-berkeley |
| 11 | Apartment List Southside page | Campus-adjacent listings and student-housing options | https://www.apartmentlist.com/ca/berkeley/neighborhoods/southside |
| 12 | Apartment List West Berkeley page | Broader neighborhood options and lower-cost rental inventory | https://www.apartmentlist.com/ca/berkeley/neighborhoods/west-berkeley |

---

## Chunking Strategy


**Chunk size:**
800 tokens

**Overlap:**
120 tokens

**Reasoning:**
These sources are mostly sectioned pages with FAQ blocks, pricing tables, and apartment cards. An 800-token chunk usually keeps one neighborhood explanation, one co-op description, or one policy subsection intact, while a small overlap preserves headings and the lead-in to tables or warning lists.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan


| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What does BSC say a room-and-board house costs per semester, and what is included? | $4,986 per semester for Fall 2026 / Spring 2027; food, utilities, cleaning supplies, furniture, and co-op-wide events are included. |
| 2 | Which BSC house is substance-free and academically themed? | Cloyne Court. |
| 3 | Name two scam red flags listed by UC Berkeley Off-Campus Rental Services. | Examples include below-market rent, requests to wire money, inability to meet in person, and dramatic landlord stories. |
| 4 | How does Apartment List describe Downtown Berkeley, and what drawback does it mention? | Urban/bustling/walkable; it warns about possible 2AM noise and limited parking during events. |
| 5 | What is the average rent for a 1-bedroom apartment in Berkeley according to Apartment List? | $2,665+ per month. |

---

## Anticipated Challenges


1. ApartmentList pages mix neighborhood summaries with large blocks of listings and images, so poor cleaning could leave the retriever focused on repeated boilerplate instead of the actual neighborhood facts.

2. The corpus includes policy pages, pricing pages, and descriptive housing pages that update at different rates, so the system could return stale price or availability information unless the final pipeline makes freshness clear.

3. BSC pages are highly house-specific, so chunking has to preserve the house name and eligibility details or answers may blend multiple co-ops together.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
