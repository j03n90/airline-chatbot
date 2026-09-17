# Evaluation cases

Same ids as `GET /api/mock/presets` and the Mock Lab list. Each catalog entry has English `starterMessage` and Chinese `starterMessageZh`. Assistant conversation tests run both (`lang=en|zh`) against the same ids and seeds; they assert quotes / reason codes, not reply wording. Assertions live in `tests/`. "Actual" is from `uv run pytest` on this revision (**99 collected**).

| id | function | expected | actual |
| --- | --- | --- | --- |
| policy_qa_sta_baggage | policy_qa | STA Basic: no domestic checked bag; 1x20kg international | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_baggage_sta_basic_domestic_vs_international` |
| policy_qa_unknown | policy_qa | Do not merge three airlines into one fee | Pass: `tests/assistant/test_assistant_api.py::test_unknown_airline_policy_does_not_pick_one_carrier` (en+zh); RAG `tests/rag/test_retrieve.py::test_unknown_airline_returns_three_groups` |
| policy_qa_pets | policy_qa | Uncovered topic, no invented fee | Pass (corpus/routing only, no assistant test): PET_LOUNGE_RE -> policy_qa; corpus sections 9/10 say contact desk |
| lookup_ok | lookup | STA85X returned after Ada Ng | Pass (mock only, no assistant test): `tests/mock/test_mock_api.py::test_lookup_requires_first_and_last` (ok path) |
| lookup_missing | lookup | not_found | Pass (mock only, no assistant test): `tests/mock/test_mock_api.py::test_lookup_requires_first_and_last` (PNR `NOPE`; catalog uses `ZZZZZZ`, same `not_found` path) |
| lookup_surname_only | lookup | identity_insufficient | Pass: `tests/assistant/test_assistant_api.py::test_lookup_surname_insufficient` (en+zh); mock `test_lookup_requires_first_and_last` |
| change_sta_standard_mixed | change | USD 85 quote; mutate only after confirm | Pass: `tests/assistant/test_assistant_api.py::test_change_sta_quote_then_confirm` (en+zh); mock `test_quote_change_does_not_mutate` / `test_confirm_change_mutates` |
| change_nsa_flex_free | change | change_fee 0 | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_nsa_flex_always_zero` |
| change_bha_basic_denied | change | not_permitted, no mutation | Pass: `tests/assistant/test_assistant_api.py::test_bha_basic_change_denied_no_mutation` (en+zh); mock `test_bha_basic_change_rejected` |
| change_bha_standard_old | change | USD 85 (issued before 2026-07-01) | Pass: `tests/assistant/test_assistant_api.py::test_bha_issuance_fees` (en+zh) |
| change_bha_standard_new | change | USD 55 (issued at cutover) | Pass: same test as previous row |
| change_bha_standard_late | change | not_permitted | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_bha_standard_late_forbidden` |
| cancel_nsa_flex | cancel | original_payment 500, extras not refundable, tax 55 | Pass: `tests/assistant/test_assistant_api.py::test_cancel_nsa_flex_quote` (en+zh) |
| cancel_sta_standard_intl | cancel | no fare refund, tax refundable | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_sta_standard_domestic_credit_25_international_none` |
| cancel_bha_standard | cancel | fare none, tax refundable | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_bha_standard_no_fare_flex_early_credit` |
| identity_other_adult | identity | Ada cannot cancel Ben | Pass: `tests/assistant/test_assistant_api.py::test_identity_other_adult` (en+zh, `not_authorized`) |
| handoff_partial | handoff | Section 9, no unused-ticket table | Pass: `tests/assistant/test_assistant_api.py::test_partial_refund_handoff` (en+zh) |
| handoff_one_segment | handoff | selected-segment cancel -> desk | Pass (engine only, no assistant test): `tests/policy/test_engine.py::test_selected_segment_cancel_handoff` |
| noshow_flex | noshow | no fare refund, tax yes | Pass: `tests/assistant/test_assistant_api.py::test_noshow_tax_only` (en+zh, `noshow`) |
| disruption_bha_120 | disruption | 120 min does not qualify on BHA | Pass: `tests/assistant/test_assistant_api.py::test_disruption_thresholds_via_cancel_quote` (en+zh); engine `test_disruption_thresholds` |
| disruption_bha_180 | disruption | 180 min qualifies, full refund incl. Basic | Pass: same assistant test (`kind=disruption_refund`); engine `test_disruption_thresholds` |

Failure paths included: identity, not_permitted, noshow, handoff, unknown PNR, unconfirmed quote does not mutate.
