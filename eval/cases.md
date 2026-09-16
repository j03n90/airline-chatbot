# Evaluation cases

Same ids as `GET /api/mock/presets` and the left pane. Assertions live in `tests/`. "Actual" is from `uv run pytest` on this revision (62 passed).

| id | function | expected | actual |
| --- | --- | --- | --- |
| policy_qa_sta_baggage | policy_qa | STA Basic: no domestic checked bag; 1x20kg international | Covered by RAG tests + engine baggage tests. Pass. |
| policy_qa_unknown | policy_qa | Do not merge three airlines into one fee | `tests/assistant/test_unknown_airline_policy_does_not_pick_one_carrier` pass. Retrieval hits >= 2 airlines. |
| policy_qa_pets | policy_qa | Uncovered topic, no invented fee | Catalog case; corpus section 9/10 says contact desk. |
| lookup_ok | lookup | STA85X returned after Ada Ng | Mock lookup tests pass. |
| lookup_missing | lookup | not_found | Mock `NOPE` lookup pass. |
| lookup_surname_only | lookup | identity_insufficient | Assistant + mock tests pass. |
| change_sta_standard_mixed | change | USD 85 quote; mutate only after confirm | Assistant test pass (85, then status=changed). |
| change_nsa_flex_free | change | change_fee 0 | Engine + catalog. |
| change_bha_basic_denied | change | not_permitted, no mutation | Assistant test pass. |
| change_bha_standard_old | change | USD 85 (issued before 2026-07-01) | Assistant test pass. |
| change_bha_standard_new | change | USD 55 (issued at cutover) | Assistant test pass. |
| change_bha_standard_late | change | not_permitted | Engine + mock. |
| cancel_nsa_flex | cancel | original_payment 500, extras not refundable, tax 55 | Assistant test pass. |
| cancel_sta_standard_intl | cancel | no fare refund, tax refundable | Engine test pass. |
| cancel_bha_standard | cancel | fare none, tax refundable | Engine test pass. |
| identity_other_adult | identity | Ada cannot cancel Ben | Assistant test `not_authorized` pass. |
| handoff_partial | handoff | Section 9, no unused-ticket table | Assistant test handoff pass. |
| handoff_one_segment | handoff | selected-segment cancel ? desk | Engine + agent segment_ids path. |
| noshow_flex | noshow | no fare refund, tax yes | Assistant test `noshow` pass. |
| disruption_bha_120 | disruption | 120 min does not qualify on BHA | Assistant test: not disruption_refund. |
| disruption_bha_180 | disruption | 180 min qualifies, full refund incl. Basic | Assistant test: kind=disruption_refund, fare 90. |

Failure paths included: identity, not_permitted, noshow, handoff, unknown PNR, unconfirmed quote does not mutate.
