import { AIRLINE_NAMES, formatUtc, isBooking, prettyLabel, usd, type Booking } from "../types";

function StatusChip({ value }: { value: string | undefined }) {
  const label = prettyLabel(value);
  const tone = (value || "unknown").toLowerCase();
  return <span className={`chip chip-${tone}`}>{label}</span>;
}

function BookingBody({ booking }: { booking: Booking }) {
  const airline = AIRLINE_NAMES[booking.airline] || booking.airline;
  return (
    <article className="booking-card glass">
      <header>
        <div>
          <p className="booking-kicker">{airline}</p>
          <h3>{booking.pnr}</h3>
        </div>
        <StatusChip value={booking.status || "active"} />
      </header>
      <p className="booking-meta">
        {prettyLabel(booking.fare_type)}
        {booking.issued_at_utc ? ` - Issued ${formatUtc(booking.issued_at_utc)}` : ""}
      </p>
      <ul className="passenger-list">
        {booking.passengers.map((person) => (
          <li key={person.id}>
            {person.first_name} {person.last_name}
            {person.is_minor ? " (minor)" : ""}
            {person.ticket_fare_usd != null ? ` - ${usd(person.ticket_fare_usd)}` : ""}
          </li>
        ))}
      </ul>
      <ol className="segment-list">
        {booking.segments.map((segment) => (
          <li key={segment.id}>
            <div className="segment-route">
              <strong>
                {segment.origin} to {segment.destination}
              </strong>
              <StatusChip value={segment.status} />
            </div>
            <p>
              {formatUtc(segment.departure_utc)}
              {segment.route_type ? ` - ${prettyLabel(segment.route_type)}` : ""}
            </p>
          </li>
        ))}
      </ol>
    </article>
  );
}

export default function BookingCard({ bookings }: { bookings: unknown[] }) {
  const rows = bookings.filter(isBooking);
  return (
    <section className="booking-section">
      <h2>Current bookings</h2>
      {rows.length === 0 ? (
        <p className="hint">Load a case to inspect itineraries here.</p>
      ) : (
        rows.map((booking) => <BookingBody key={booking.pnr} booking={booking} />)
      )}
      <details className="raw-json">
        <summary>Raw JSON</summary>
        <pre>{JSON.stringify(bookings, null, 2)}</pre>
      </details>
    </section>
  );
}
