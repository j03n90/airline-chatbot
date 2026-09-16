import { useMemo, useState } from "react";
import { CUSTOM_CASE, type TestCase } from "../testCases";
import { prettyLabel } from "../types";

type Props = {
  cases: TestCase[];
  activeId: string | null;
  customJson: string;
  busy: boolean;
  hasConversation: boolean;
  onCustomJson: (value: string) => void;
  onLoad: (item: TestCase) => void;
};

export default function CaseList({
  cases,
  activeId,
  customJson,
  busy,
  hasConversation,
  onCustomJson,
  onLoad,
}: Props) {
  const [pending, setPending] = useState<TestCase | null>(null);

  const groups = useMemo(() => {
    const map = new Map<string, TestCase[]>();
    for (const item of cases) {
      const key = item.function || "other";
      const list = map.get(key) ?? [];
      list.push(item);
      map.set(key, list);
    }
    return [...map.entries()];
  }, [cases]);

  function requestLoad(item: TestCase) {
    if (busy) return;
    if (hasConversation) {
      setPending(item);
      return;
    }
    onLoad(item);
  }

  return (
    <section className="case-section">
      <p className="hint">Pick a seed, then send the prefilled message in chat.</p>
      {groups.map(([fn, items]) => (
        <div key={fn} className="grouped-list">
          <h3>{prettyLabel(fn)}</h3>
          <div className="grouped-body glass">
            {items.map((item, index) => (
              <button
                key={item.id}
                type="button"
                className={`case ${item.id === activeId ? "active" : ""} ${index === items.length - 1 ? "last" : ""}`}
                onClick={() => requestLoad(item)}
                disabled={busy}
              >
                <span className="case-title">{item.title}</span>
                <span className="case-expected">{item.expected}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
      {activeId === CUSTOM_CASE.id ? (
        <div className="custom-seed">
          <label htmlFor="custom-json">Custom seed JSON</label>
          <textarea
            id="custom-json"
            value={customJson}
            onChange={(event) => onCustomJson(event.target.value)}
            rows={10}
            spellCheck={false}
          />
          <button type="button" className="text-btn" disabled={busy} onClick={() => requestLoad(CUSTOM_CASE)}>
            Load seed
          </button>
        </div>
      ) : null}

      {pending ? (
        <div className="alert-backdrop" role="presentation" onClick={() => setPending(null)}>
          <div
            className="alert glass"
            role="dialog"
            aria-labelledby="case-alert-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="case-alert-title">Start a new case?</h3>
            <p>This clears the current conversation and loads a fresh mock session.</p>
            <div className="alert-actions">
              <button type="button" onClick={() => setPending(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="alert-confirm"
                onClick={() => {
                  const item = pending;
                  setPending(null);
                  onLoad(item);
                }}
              >
                Load
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
