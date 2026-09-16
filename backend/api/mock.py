from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    BookingsResponse,
    ClockResponse,
    ClockUpdateRequest,
    ConfirmRequest,
    ConfirmResponse,
    LoadRequest,
    LookupRequest,
    LookupResponse,
    OkMessage,
    QuoteCancelRequest,
    QuoteChangeRequest,
    QuoteResult,
    ReasonCode,
    SeedPayload,
)
from backend.mock.seeds import CASE_CATALOG, SEEDS
from backend.mock.store import store

router = APIRouter(prefix="/api/mock", tags=["mock"])


@router.get("/presets")
def presets():
    items = []
    for case in CASE_CATALOG:
        payload = SEEDS[case["id"]]
        items.append({**case, "seed": payload.model_dump(mode="json")})
    return {"cases": items}


@router.post("/sessions/{session_id}/load-preset")
def load_preset(session_id: str, preset_id: str):
    if preset_id not in SEEDS:
        raise HTTPException(status_code=404, detail="unknown_preset")
    state = store.load(session_id, SEEDS[preset_id])
    meta = next(c for c in CASE_CATALOG if c["id"] == preset_id)
    return {
        "now_utc": state.now.isoformat(),
        "bookings": [b.model_dump(mode="json") for b in state.bookings.values()],
        "case": meta,
    }


@router.post("/sessions/{session_id}/load", response_model=BookingsResponse)
def load_session(session_id: str, body: LoadRequest) -> BookingsResponse:
    state = store.load(session_id, SeedPayload(now_utc=body.now_utc, bookings=body.bookings))
    return BookingsResponse(now_utc=state.now, bookings=list(state.bookings.values()))


@router.post("/sessions/{session_id}/reset", response_model=OkMessage)
def reset_session(session_id: str) -> OkMessage:
    store.reset(session_id)
    return OkMessage(message="Session cleared.")


@router.get("/sessions/{session_id}/clock", response_model=ClockResponse)
def get_clock(session_id: str) -> ClockResponse:
    return ClockResponse(now_utc=store.session(session_id).now)


@router.put("/sessions/{session_id}/clock", response_model=ClockResponse)
def set_clock(session_id: str, body: ClockUpdateRequest) -> ClockResponse:
    now = store.set_clock(session_id, body.now_utc)
    return ClockResponse(now_utc=now)


@router.get("/sessions/{session_id}/bookings", response_model=BookingsResponse)
def list_bookings(session_id: str) -> BookingsResponse:
    state = store.session(session_id)
    return BookingsResponse(now_utc=state.now, bookings=list(state.bookings.values()))


@router.post("/sessions/{session_id}/lookup", response_model=LookupResponse)
def lookup(session_id: str, body: LookupRequest) -> LookupResponse:
    return store.lookup(session_id, body.pnr, body.last_name, body.first_name)


@router.post("/sessions/{session_id}/quote-change", response_model=QuoteResult)
def quote_change(session_id: str, body: QuoteChangeRequest) -> QuoteResult:
    return store.quote_change(session_id, body)


@router.post("/sessions/{session_id}/quote-cancel", response_model=QuoteResult)
def quote_cancel(session_id: str, body: QuoteCancelRequest) -> QuoteResult:
    return store.quote_cancel(session_id, body)


@router.get("/sessions/{session_id}/quotes/{quote_id}", response_model=QuoteResult)
def get_quote(session_id: str, quote_id: str) -> QuoteResult:
    quote = store.get_quote(session_id, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail=ReasonCode.QUOTE_NOT_FOUND.value)
    return quote


@router.post("/sessions/{session_id}/confirm", response_model=ConfirmResponse)
def confirm(session_id: str, body: ConfirmRequest) -> ConfirmResponse:
    return store.confirm(session_id, body.quote_id, body.passenger_id, body.first_name, body.last_name)
