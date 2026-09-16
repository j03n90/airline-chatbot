import type { Quote } from "../types";
import { prettyLabel, usd } from "../types";

export default function QuoteCard({ quote }: { quote: Quote }) {
  const ok = quote.ok !== false;
  const kind = prettyLabel(quote.kind || "quote");
  const headline =
    quote.total_due_usd != null
      ? usd(quote.total_due_usd)
      : quote.fare_refund_usd
        ? `${usd(quote.fare_refund_usd)} refund`
        : prettyLabel(quote.reason_code);

  return (
    <div className={`quote-card glass ${ok ? "ok" : "blocked"}`}>
      <p className="quote-kicker">{ok ? "Pending quote" : "Quote not applied"}</p>
      <h3>{headline}</h3>
      <p className="quote-kind">{kind}</p>
      <dl>
        {quote.change_fee_usd != null ? (
          <>
            <dt>Change fee</dt>
            <dd>{usd(quote.change_fee_usd)}</dd>
          </>
        ) : null}
        {quote.fare_difference_usd != null && quote.kind === "change" ? (
          <>
            <dt>Fare difference</dt>
            <dd>{usd(quote.fare_difference_usd)}</dd>
          </>
        ) : null}
        {quote.fare_refund_usd != null && quote.kind !== "change" ? (
          <>
            <dt>Fare refund</dt>
            <dd>{usd(quote.fare_refund_usd)}</dd>
          </>
        ) : null}
        {quote.tax_refund_usd != null && (quote.tax_refund_usd > 0 || quote.kind !== "change") ? (
          <>
            <dt>Tax refund</dt>
            <dd>{usd(quote.tax_refund_usd)}</dd>
          </>
        ) : null}
        {quote.reason_code ? (
          <>
            <dt>Reason</dt>
            <dd>{quote.reason_code}</dd>
          </>
        ) : null}
      </dl>
      <p className="quote-note">Not applied until the traveler confirms in chat.</p>
    </div>
  );
}
