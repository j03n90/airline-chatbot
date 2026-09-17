import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import BookingCard from "./components/BookingCard";
import CaseList from "./components/CaseList";
import ChatPane from "./components/ChatPane";
import LabDrawer from "./components/LabDrawer";
import {
  chatOnce,
  createAssistantSession,
  listBookings,
  listPresets,
  loadPreset,
  loadSeed,
} from "./api";
import { CUSTOM_CASE, type TestCase } from "./testCases";
import { readTheme, toggleTheme, type Theme } from "./theme";
import type { Booking, Msg, Quote } from "./types";

const EMPTY_SEED = `{
  "now_utc": "2026-09-16T12:00:00+00:00",
  "bookings": []
}`;

export default function App() {
  const [cases, setCases] = useState<TestCase[]>([CUSTOM_CASE]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mockSession, setMockSession] = useState(() => crypto.randomUUID());
  const [assistantSession, setAssistantSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [customJson, setCustomJson] = useState(EMPTY_SEED);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [handoff, setHandoff] = useState(false);
  const [busy, setBusy] = useState(false);
  const [labOpen, setLabOpen] = useState(false);
  const [status, setStatus] = useState("Open Lab to load a test case.");
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [theme, setTheme] = useState<Theme>(() => readTheme());
  const bootMockId = useRef(mockSession);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      for (let attempt = 0; attempt < 5; attempt += 1) {
        try {
          const data = await listPresets();
          if (!cancelled) setCases([...data.cases, CUSTOM_CASE]);
          return;
        } catch (err) {
          if (attempt === 4 && !cancelled) {
            setStatus(`Could not load presets: ${err}`);
          } else {
            await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
          }
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        const created = await createAssistantSession(bootMockId.current);
        if (!cancelled) {
          setAssistantSession((current) => current ?? created.session_id);
        }
      } catch {
        // Header falls back to the client mock session id.
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  const onToggleLab = useCallback(() => {
    setLabOpen((open) => !open);
  }, []);

  const onToggleTheme = useCallback(() => {
    setTheme((current) => toggleTheme(current));
  }, []);

  async function refreshBookings(id: string) {
    const data = await listBookings(id);
    setBookings(data.bookings);
  }

  async function newAssistant(mockId: string) {
    const created = await createAssistantSession(mockId);
    setAssistantSession(created.session_id);
    setMessages([]);
    setQuote(null);
    setHandoff(false);
    return created.session_id;
  }

  async function loadCase(item: TestCase) {
    setBusy(true);
    try {
      const mockId = crypto.randomUUID();
      setMockSession(mockId);
      setActiveId(item.id);
      if (item.id === "custom") {
        await loadSeed(mockId, customJson);
      } else {
        await loadPreset(mockId, item.id);
      }
      await newAssistant(mockId);
      await refreshBookings(mockId);
      setDraft(item.starterMessage);
      setStatus(`Loaded ${item.id}. Expected: ${item.expected}`);
      setLabOpen(true);
    } catch (err) {
      setStatus(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || busy) return;
    let sid = assistantSession;
    if (!sid) {
      sid = await newAssistant(mockSession);
    }
    const text = draft;
    setDraft("");
    setMessages((current) => [...current, { role: "user", text }]);
    setBusy(true);
    try {
      const result = await chatOnce(sid, text);
      setMessages((current) => [...current, { role: "assistant", text: result.text }]);
      setQuote(result.pending_quote);
      setHandoff(result.handoff);
      await refreshBookings(mockSession);
    } catch (err) {
      setMessages((current) => [...current, { role: "assistant", text: String(err) }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`shell ${labOpen ? "lab-open" : ""}`}>
      <div className="ambient" aria-hidden="true">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
        <span className="orb orb-c" />
      </div>
      <ChatPane
        sessionId={assistantSession ?? mockSession}
        status={status}
        labOpen={labOpen}
        onToggleLab={onToggleLab}
        theme={theme}
        onToggleTheme={onToggleTheme}
        messages={messages}
        quote={quote}
        handoff={handoff}
        loaded={activeId !== null}
        busy={busy}
        draft={draft}
        onDraft={setDraft}
        onSend={onSend}
      />
      <LabDrawer open={labOpen} onToggle={onToggleLab}>
        <CaseList
          cases={cases}
          activeId={activeId}
          customJson={customJson}
          busy={busy}
          hasConversation={messages.length > 0}
          onCustomJson={setCustomJson}
          onLoad={loadCase}
        />
        <BookingCard bookings={bookings} />
      </LabDrawer>
    </div>
  );
}
