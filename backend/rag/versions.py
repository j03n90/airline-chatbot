from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def parse_utc(value: datetime | str | None) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def select_applicable_chunks(docs: list[dict], as_of: datetime | str | None = None) -> list[dict]:
    """Keep only the latest in-force version per airline.

    A version is in force when ``effective_at <= as_of``. If ``as_of`` is omitted,
    the newest version of each airline is kept so historical editions do not mix
    into untimed queries.
    """
    as_of_dt = parse_utc(as_of)
    by_airline: dict[str, list[dict]] = {}
    for doc in docs:
        by_airline.setdefault(doc.get("airline_code") or "", []).append(doc)

    selected: list[dict] = []
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    for chunks in by_airline.values():
        eligible = []
        for chunk in chunks:
            effective = parse_utc(chunk.get("effective_at"))
            if effective is None:
                eligible.append(chunk)
                continue
            if as_of_dt is None or effective <= as_of_dt:
                eligible.append(chunk)
        if not eligible:
            continue

        def effective_key(chunk: dict) -> datetime:
            return parse_utc(chunk.get("effective_at")) or epoch

        latest_effective = max(effective_key(chunk) for chunk in eligible)
        latest_versions = {
            chunk.get("version") for chunk in eligible if effective_key(chunk) == latest_effective
        }
        selected.extend(chunk for chunk in eligible if chunk.get("version") in latest_versions)
    return selected
