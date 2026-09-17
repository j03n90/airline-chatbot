# Execution trace: unknown-airline Economy Basic change fee

Preset `policy_qa_unknown`. No booking is loaded (`SEED_EMPTY`). The traveler does not name an airline. Clock is the mock session clock at load time.

## User 1

"How much does it cost to change an Economy Basic ticket?"

### Sources retrieved

`retrieve_policy` searched all three FAISS indexes (`airline=None`). Hits returned, highest score first (compose uses the first eight):

1. Northstar Air (NSA) v2.0 effective 2026-01-01 -- Section 2.1 Change fee schedule -- page 2
2. Suntrail Air (STA) v1.4 effective 2026-03-01 -- Section 2.1 Change fee schedule -- page 2
3. Bluehaven Airways (BHA) v3.0 effective 2026-07-01 -- Section 2.1 Change fee schedule -- page 2
4. Bluehaven Airways (BHA) v3.0 effective 2026-07-01 -- Appendix A Economy Standard change-fee update -- page 6
5. Bluehaven Airways (BHA) v3.0 effective 2026-07-01 -- Section 7 Cabin and checked baggage -- page 5
6. Northstar Air (NSA) v2.0 effective 2026-01-01 -- Section 3 Voluntary cancellation and refunds -- page 3
7. Suntrail Air (STA) v1.4 effective 2026-03-01 -- Section 6 Airline-initiated disruptions -- page 4
8. Northstar Air (NSA) v2.0 effective 2026-01-01 -- Section 6 Airline-initiated disruptions -- page 4

### Actions

1. `ingest_turn` -- no PNR, no airline hint
2. `route_intent` -- `policy_qa` (fee question, no PNR)
3. `retrieve_policy` -- request `{airline: null}`; returned the sources above (at least two airlines; usually all three)
4. `compose_reply` -- Facts include the policy sources plus: Airline is unknown. Explain that rules differ by airline. Do not merge them into one rule.

Assistant answers per carrier (STA Basic international not permitted / NSA Basic USD 70 early / BHA Basic not permitted) rather than one fake global fee. Handoff: none.

No hidden chain-of-thought is stored on `GET /api/assistant/sessions/{id}/trace` -- only tool names, request fields, reason codes, and retrieval metadata (airline, section, title, page, version).
