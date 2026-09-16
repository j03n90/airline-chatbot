export type Msg = { role: "user" | "assistant"; text: string };

export type Quote = {
  ok?: boolean;
  reason_code?: string;
  quote_id?: string | null;
  kind?: string | null;
  change_fee_usd?: number;
  fare_difference_usd?: number;
  total_due_usd?: number;
  refund_type?: string;
  fare_refund_usd?: number;
  tax_refund_usd?: number;
  extras_refundable?: boolean;
  extras_refund_usd?: number;
  window?: string | null;
  itinerary_route_type?: string | null;
  message?: string;
  breakdown?: Record<string, unknown>[];
  handoff_reason?: string | null;
};

export type Passenger = {
  id: string;
  first_name: string;
  last_name: string;
  is_minor?: boolean;
  ticket_fare_usd?: number;
  government_tax_usd?: number;
};

export type Segment = {
  id: string;
  origin: string;
  destination: string;
  departure_utc: string;
  arrival_utc: string;
  route_type?: string;
  fare_usd?: number;
  status?: string;
};

export type Booking = {
  pnr: string;
  airline: string;
  fare_type: string;
  issued_at_utc?: string;
  channel?: string;
  status?: string;
  passengers: Passenger[];
  segments: Segment[];
  extras?: unknown[];
  travel_credit_usd?: number;
  notes?: string;
};

export const AIRLINE_NAMES: Record<string, string> = {
  STA: "Suntrail Air",
  NSA: "Northstar Air",
  BHA: "Bluehaven Airways",
};

export function isBooking(value: unknown): value is Booking {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return typeof row.pnr === "string" && Array.isArray(row.passengers) && Array.isArray(row.segments);
}

export function usd(amount: number | undefined): string {
  if (amount == null || Number.isNaN(amount)) return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

export function prettyLabel(value: string | undefined | null): string {
  if (!value) return "-";
  const special: Record<string, string> = {
    policy_qa: "Policy Q&A",
    noshow: "No-show",
  };
  if (special[value]) return special[value];
  return value.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export function formatUtc(iso: string | undefined): string {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "UTC",
  })} UTC`;
}
