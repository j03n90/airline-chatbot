from pathlib import Path

import pytest

from backend.config import settings
from backend.rag.ingest import build_indexes
from backend.rag.retrieve import load_indexes, retrieve


@pytest.fixture(scope="module")
def built_index(tmp_path_factory):
    index_dir = tmp_path_factory.mktemp("faiss")
    build_indexes(index_dir)
    load_indexes(index_dir)
    return index_dir


def test_known_airline_does_not_mix(built_index):
    hits = retrieve("Economy Basic checked baggage domestic allowance", airline="STA", k=4)
    assert hits
    assert all(h["airline_code"] == "STA" for h in hits)
    blob = " ".join(h["text"].lower() for h in hits)
    assert "northstar" not in blob
    assert "20 kg" in blob or "none" in blob


def test_unknown_airline_returns_three_groups(built_index):
    hits = retrieve("Economy Basic cabin bag allowance", airline=None, k=2)
    codes = {h["airline_code"] for h in hits}
    assert codes == {"STA", "NSA", "BHA"}


def test_change_fee_tables_retrieved_intact(built_index):
    sta = retrieve("voluntary change fee schedule Economy Standard international", airline="STA")
    assert any(h["kind"] == "table" and "2.1" in h["section"] for h in sta)
    assert any("USD 65" in h["text"] for h in sta)


def test_bha_appendix_a_issuance_rule(built_index):
    hits = retrieve("Standard change fee issued before July 2026 Appendix A", airline="BHA", k=4)
    text = " ".join(h["text"] for h in hits)
    assert "85" in text
    assert "2026-07-01" in text
    assert any("Appendix" in h["section"] or "Appendix" in h["title"] for h in hits)


def test_bha_disruption_180_not_120(built_index):
    hits = retrieve("schedule change qualifying minutes disruption", airline="BHA")
    text = " ".join(h["text"] for h in hits)
    assert "180" in text


def test_ownership_pnr_surname_not_enough(built_index):
    hits = retrieve("is a booking reference and surname enough authority", airline="NSA")
    text = " ".join(h["text"].lower() for h in hits)
    assert "not authority" in text or "surname" in text
