# Design notes

Time spent: about 6 hours on the focused implementation (two HTTP surfaces, policy engine, FAISS indexes, LangGraph graph, UI lab, and layered tests). We stopped expanding product features at that cap; leftover time went to tests and this writeup. Deliberately left-out capabilities are listed under Limitations.

## Scenarios we prioritized

Travelers do not name the airline first, and the three PDFs share headings while disagreeing on money. The product risk is mixing carriers, inventing fees, or mutating a booking without a confirmed quote.

We implemented, and tested, in this order:

1. Deterministic change/cancel/baggage/disruption tables
2. Stateful mock booking API (quote does not mutate; confirm does)
3. Per-airline FAISS retrieval
4. LangGraph: lookup -> quote -> confirm / handoff
5. A left-pane lab so a reviewer can load the same cases the tests use

## Assumptions

- **Direct bookings, named adult only.** Agency-issued tickets, written representatives, and guardianship evidence go to the service desk (PDF section 8 / 8.1). The mock `channel` field defaults to `direct` and is not a separate flow.
- **Concurrent use is session isolation, not a shared booking database.** Each reviewer/demo gets a `mock_session_id` plus a LangGraph `thread_id`. The mock store is an in-process dict with no cross-request lock. One process is enough for the trial UI. A process restart drops bookings; Sqlite may still hold a leftover quote that cannot be confirmed against an empty mock.
- **Policy PDFs are transcribed, not parsed.** [`backend/rag/corpus.py`](backend/rag/corpus.py) is a curated chunking of the three `Passenger_Policies.pdf` files (tables kept whole so fee rows cannot split). [`backend/rag/ingest.py`](backend/rag/ingest.py) embeds that corpus with MiniLM. Runtime never reads the PDF bytes. If a PDF and the corpus drifted, retrieval would not notice.
- **PNR extraction** prefers the demo catalog ids, then a 6-character token that contains a digit. An all-letter custom PNR may not be picked up from chat.
- **Change quotes copy the existing segment fare**, so fare difference is USD 0 on the demo path.

## Main decisions

- **Two APIs in one process.** The assistant never imports the mock store; it goes through `MockClient`. Tests can exercise bookings without an LLM.
- **RAG does not compute money.** MiniLM + three FAISS indexes answer "what does the PDF say". `backend/policy/engine.py` computes fees. That split is why STA Standard mixed-route changes stay at USD 20+65=85.
- **Local MiniLM, not the chat API, for embeddings.** The corpus is tiny and English. Indexes are built with `uv run python -m backend.rag.ingest`.
- **Python packaging is uv only** (`pyproject.toml` + `uv.lock`). Interviewers should not `pip install -r`.
- **LangGraph is a visible state machine** (ingest, route, retrieve/lookup/quote/confirm, compose), not a single ReAct blob.
- **Short-term memory is a LangGraph checkpointer** keyed by `thread_id` (Sqlite on the app, in-memory in tests). It is not a hand-rolled session dict and not a long-term Memory Server / Store.
- **Identity is strict.** PNR + surname is `identity_insufficient`. One adult cannot operate another adult's ticket.

## How we know it works

`uv run pytest` collects 99 tests covering the fee matrix, mock state, retrieval isolation, routing, LangGraph thread checkpoints, and assistant conversations (success, denial, handoff, no-show, issuance-date fees). See [eval/cases.md](eval/cases.md). Execution traces: [change then confirm](eval/trace-one-conversation.md) and [unknown-airline policy QA (with sources)](eval/trace-policy-qa-unknown.md).

## Limitations / deliberately left out

Stopped here on purpose; these are not accidental omissions:

- Change requests currently move every remaining segment by +1 day (enough to demonstrate the fee table; not a full calendar search or arbitrary date parse).
- After travel has started, changing remaining unflown segments is not a demonstrated success path (a flown segment on the ticket becomes a desk handoff).
- Disruption support is a qualifying **refund** only. PDF section 6.2 replacement travel (one rebooking within 7 calendar days, no change fee or fare difference) is not an agent action, even though `DISRUPTION_REBOOK` exists on the quote schema.
- The 30-elapsed-day disruption request window is not enforced.
- Travel-credit expiry (365 elapsed days) is stated in the corpus; there is no stored credit object or redemption clock.
- PDF section 7.2 overweight / oversized / dangerous goods is not in the corpus. Those questions should go to the desk; we do not invent a fee.
- Purchased extras do not transfer onto a changed itinerary (PDF section 3.2).
- Disruption hotel/meal/ground-transport compensation is unspecified in the PDFs and not invented.
- Pets, lounge, loyalty, unaccompanied minors: we refuse and point to the desk (PDF section 10).
- Sqlite checkpoints persist the conversation thread; the mock booking store is still in-process. Production would persist both the same way. There is no long-term user memory.
- Visual polish was not a goal.
