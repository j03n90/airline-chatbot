# Design notes

Time spent: focused implementation of the two HTTP surfaces, policy engine, FAISS indexes, LangGraph graph, UI lab, and layered tests.

## Scenarios we prioritized

Travelers do not name the airline first, and the three PDFs share headings while disagreeing on money. The product risk is mixing carriers, inventing fees, or mutating a booking without a confirmed quote.

We implemented, and tested, in this order:

1. Deterministic change/cancel/baggage/disruption tables
2. Stateful mock booking API (quote does not mutate; confirm does)
3. Per-airline FAISS retrieval
4. LangGraph: lookup ? quote ? confirm / handoff
5. A left-pane lab so a reviewer can load the same cases the tests use

## Main decisions

- **Two APIs in one image.** The assistant never imports the mock store; it goes through `MockClient`. Tests can exercise bookings without an LLM.
- **RAG does not compute money.** MiniLM + three FAISS indexes answer "what does the PDF say". `backend/policy/engine.py` computes fees. That split is why STA Standard mixed-route changes stay at USD 20+65=85.
- **Local MiniLM, not DeepSeek, for embeddings.** The corpus is tiny and English. Indexes are built with `uv run python -m backend.rag.ingest` and again in Docker.
- **Python packaging is uv only** (`pyproject.toml` + `uv.lock`). Interviewers should not `pip install -r`.
- **LangGraph is a visible state machine** (ingest, route, retrieve/lookup/quote/confirm, compose), not a single ReAct blob.
- **Short-term memory is a LangGraph checkpointer** keyed by `thread_id` (Sqlite on the app, in-memory in tests). It is not a hand-rolled session dict and not a long-term Memory Server / Store.
- **Identity is strict.** PNR + surname is `identity_insufficient`. One adult cannot operate another adult's ticket.

## How we know it works

`uv run pytest` ù 70 tests covering the fee matrix, mock state, retrieval isolation, routing, LangGraph thread checkpoints, and assistant conversations (success, denial, handoff, no-show, issuance-date fees). See [eval/cases.md](eval/cases.md). One full change+confirm trace is in [eval/trace-one-conversation.md](eval/trace-one-conversation.md).

## Limitations / next

- Change requests currently move every remaining segment by +1 day (enough to demonstrate the fee table; not a full calendar search).
- Disruption hotel/meal compensation is unspecified in the PDFs and not invented.
- Sqlite checkpoints persist the conversation thread; the mock booking store is still in-process. A process restart drops bookings, so a leftover quote in sqlite cannot be confirmed against an empty mock. Production would swap Sqlite for Postgres and persist the booking world the same way. There is no long-term user memory.
- Visual polish was not a goal.
- Pets, lounge, loyalty, unaccompanied minors: we refuse and point to the desk.
