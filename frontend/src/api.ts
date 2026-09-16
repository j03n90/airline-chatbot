import type { Booking, Quote } from "./types";
import type { TestCase } from "./testCases";

export async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export async function chatOnce(
  sessionId: string,
  message: string,
): Promise<{
  text: string;
  handoff: boolean;
  pending_quote: Quote | null;
}> {
  const res = await fetch("/api/assistant/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export function listPresets() {
  return getJson<{ cases: TestCase[] }>("/api/mock/presets");
}

export function loadPreset(sessionId: string, presetId: string) {
  return getJson(`/api/mock/sessions/${sessionId}/load-preset?preset_id=${encodeURIComponent(presetId)}`, {
    method: "POST",
  });
}

export function loadSeed(sessionId: string, json: string) {
  return getJson(`/api/mock/sessions/${sessionId}/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: json,
  });
}

export function listBookings(sessionId: string) {
  return getJson<{ bookings: Booking[]; now_utc?: string }>(`/api/mock/sessions/${sessionId}/bookings`);
}

export function createAssistantSession(mockId: string) {
  return getJson<{ session_id: string }>("/api/assistant/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mock_session_id: mockId }),
  });
}
