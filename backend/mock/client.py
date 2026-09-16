from backend.mock.store import store
from backend.api.schemas import (
    ConfirmRequest,
    LookupRequest,
    QuoteCancelRequest,
    QuoteChangeRequest,
    SeedPayload,
)


class MockClient:
    """The only way the assistant touches bookings. Wraps the mock store."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def load(self, payload: SeedPayload):
        return store.load(self.session_id, payload)

    def clock(self):
        return store.session(self.session_id).now

    def lookup(self, pnr: str, last_name: str, first_name: str | None):
        return store.lookup(self.session_id, pnr, last_name, first_name)

    def quote_change(self, req: QuoteChangeRequest):
        return store.quote_change(self.session_id, req)

    def quote_cancel(self, req: QuoteCancelRequest):
        return store.quote_cancel(self.session_id, req)

    def confirm(self, req: ConfirmRequest):
        return store.confirm(self.session_id, req.quote_id, req.passenger_id, req.first_name, req.last_name)

    def bookings(self):
        return store.list_bookings(self.session_id)
