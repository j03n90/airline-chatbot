import { FormEvent, KeyboardEvent, useEffect, useRef } from "react";
import type { Theme } from "../theme";
import type { Msg, Quote } from "../types";
import MarkdownMessage from "./MarkdownMessage";
import QuoteCard from "./QuoteCard";

type Props = {
  status: string;
  labOpen: boolean;
  onToggleLab: () => void;
  theme: Theme;
  onToggleTheme: () => void;
  messages: Msg[];
  quote: Quote | null;
  handoff: boolean;
  loaded: boolean;
  busy: boolean;
  draft: string;
  onDraft: (value: string) => void;
  onSend: (event: FormEvent) => void;
};

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path fill="currentColor" d="M12 4.5 5.8 10.7a1 1 0 0 0 1.4 1.4L11 8.3V19a1 1 0 1 0 2 0V8.3l3.8 3.8a1 1 0 0 0 1.4-1.4L12 4.5Z" />
    </svg>
  );
}

function PlaneIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        fill="currentColor"
        d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2 1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5L21 16z"
      />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <rect x="11" y="10.5" width="2" height="6.5" rx="1" fill="currentColor" />
      <circle cx="12" cy="7.5" r="1.15" fill="currentColor" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        d="M12 3.5v1.8M12 18.7v1.8M3.5 12h1.8M18.7 12h1.8M6 6l1.3 1.3M16.7 16.7 18 18M18 6l-1.3 1.3M7.3 16.7 6 18"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
        d="M15.2 4.4A7.6 7.6 0 1 0 19.6 15 6.2 6.2 0 0 1 15.2 4.4Z"
      />
    </svg>
  );
}

export default function ChatPane({
  status,
  labOpen,
  onToggleLab,
  theme,
  onToggleTheme,
  messages,
  quote,
  handoff,
  loaded,
  busy,
  draft,
  onDraft,
  onSend,
}: Props) {
  const paneRef = useRef<HTMLElement>(null);
  const logRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const canSend = Boolean(draft.trim()) && !busy;
  const empty = !loaded && messages.length === 0 && !busy && !quote && !handoff;

  useEffect(() => {
    const node = paneRef.current;
    if (!node) return;
    node.inert = labOpen;
  }, [labOpen]);

  useEffect(() => {
    const node = logRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, [messages, quote, busy, handoff]);

  useEffect(() => {
    const node = inputRef.current;
    if (!node) return;
    node.style.height = "auto";
    node.style.height = `${Math.min(node.scrollHeight, 120)}px`;
  }, [draft]);

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }

  return (
    <main className="chat-pane" ref={paneRef}>
      <header className="chat-header glass">
        <div className="chat-identity">
          <span className="avatar" aria-hidden="true">
            <PlaneIcon />
          </span>
          <div>
            <h1>Airline Assistant</h1>
            <p>{status}</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="icon-btn glass"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Light mode" : "Dark mode"}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
          <button
            type="button"
            className={`icon-btn glass ${labOpen ? "active" : ""}`}
            onClick={onToggleLab}
            aria-label={labOpen ? "Hide Mock lab" : "Show Mock lab"}
            title="Mock lab"
          >
            <InfoIcon />
          </button>
        </div>
      </header>

      <section className="log" ref={logRef}>
        {empty ? (
          <div className="empty-state">
            <span className="empty-mark glass" aria-hidden="true">
              <PlaneIcon />
            </span>
            <h2>Airline Assistant</h2>
            <p>Ask about a booking, change, or refund. Open Lab to load a test case first.</p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <article key={`${msg.role}-${index}`} className={`bubble ${msg.role}`}>
                {msg.role === "assistant" ? <MarkdownMessage text={msg.text} /> : <p>{msg.text}</p>}
              </article>
            ))}
            {busy && messages.length > 0 ? (
              <article className="bubble assistant typing" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </article>
            ) : null}
            {quote ? <QuoteCard quote={quote} /> : null}
            {handoff ? <p className="system-banner">This request was transferred to the airline service desk.</p> : null}
          </>
        )}
      </section>

      <form className="composer glass" onSubmit={onSend}>
        <textarea
          ref={inputRef}
          value={draft}
          onChange={(event) => onDraft(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message"
          rows={1}
          disabled={busy}
          aria-label="Message"
        />
        <button type="submit" className="send-btn" disabled={!canSend} aria-label="Send">
          <SendIcon />
        </button>
      </form>
    </main>
  );
}
