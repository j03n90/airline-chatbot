from backend.rag.versions import select_applicable_chunks


def _chunk(airline: str, version: str, effective_at: str, marker: str) -> dict:
    return {
        "airline_code": airline,
        "version": version,
        "effective_at": effective_at,
        "text": marker,
        "section": "1",
    }


A = _chunk("STA", "1.3", "2026-01-01T00:00:00+00:00", "OLD_VERSION_MARKER_A")
B = _chunk("STA", "1.4", "2026-07-01T00:00:00+00:00", "NEW_VERSION_MARKER_B")
NSA = _chunk("NSA", "2.0", "2026-01-01T00:00:00+00:00", "NSA_ONLY")


def test_between_versions_keeps_a_drops_b():
    hits = select_applicable_chunks([A, B], as_of="2026-05-01T00:00:00+00:00")
    assert [h["version"] for h in hits] == ["1.3"]
    blob = " ".join(h["text"] for h in hits)
    assert "OLD_VERSION_MARKER_A" in blob
    assert "NEW_VERSION_MARKER_B" not in blob


def test_after_cutover_keeps_only_latest():
    hits = select_applicable_chunks([A, B], as_of="2026-09-16T12:00:00+00:00")
    assert [h["version"] for h in hits] == ["1.4"]
    assert "NEW_VERSION_MARKER_B" in hits[0]["text"]
    assert "OLD_VERSION_MARKER_A" not in " ".join(h["text"] for h in hits)


def test_untimed_query_uses_latest_not_historical():
    hits = select_applicable_chunks([A, B], as_of=None)
    assert [h["version"] for h in hits] == ["1.4"]


def test_before_any_version_is_empty():
    assert select_applicable_chunks([A, B], as_of="2025-12-01T00:00:00+00:00") == []


def test_effective_on_the_cutover_instant():
    hits = select_applicable_chunks([A, B], as_of="2026-07-01T00:00:00+00:00")
    assert [h["version"] for h in hits] == ["1.4"]


def test_per_airline_independence():
    hits = select_applicable_chunks([A, B, NSA], as_of="2026-05-01T00:00:00+00:00")
    by_code = {h["airline_code"]: h["version"] for h in hits}
    assert by_code == {"STA": "1.3", "NSA": "2.0"}
