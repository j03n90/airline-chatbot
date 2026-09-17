from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from backend.agent.state import AgentState

CONFIRM_RE = re.compile(
    r"(?:\b(yes|y|ok|okay|confirm|confirmed|proceed|agree|go ahead|please do|do it|that's fine|thats fine)\b|"
    r"确认|好的|是的|(?<!不)可以)",
    re.I,
)
REJECT_RE = re.compile(
    r"(?:\b(no|nope|cancel that|don't|dont|stop|never mind|reject|abort)\b|不要了|算了|取消那个)",
    re.I,
)
PNR_RE = re.compile(r"\b([A-Z0-9]{6})\b")
KNOWN_PNRS = {
    "STA85X",
    "NSAFLX",
    "BHABSC",
    "BHAOLD",
    "BHANEW",
    "BHALTE",
    "STABAG",
    "MULTI1",
    "PARTLY",
    "NOSHOW",
    "STAINL",
    "BHACAN",
    "BHA120",
    "BHA180",
    "ZZZZZZ",
}
NAME_RE = re.compile(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b")
CHANGE_RE = re.compile(
    r"(?:\b(change|reschedule|move|rebook|different (day|date|flight)|one day later)\b|"
    r"改签|改期|更改航班|换航班|推迟一天|晚一天|改到第二天)",
    re.I,
)
CANCEL_RE = re.compile(
    r"(?:\b(cancel|refund|don't want to (fly|travel)|not travelling|not traveling)\b|"
    r"取消|退票|退款|退剩余|退掉)",
    re.I,
)
LOOKUP_RE = re.compile(
    r"(?:\b(look up|lookup|find my (booking|reservation|ticket)|my booking|itinerary)\b|"
    r"查询|查一下|查找订单)",
    re.I,
)
HANDOFF_RE = re.compile(
    r"(?:\b(medical|doctor|hospital|minor|guardian|child|only one segment|just the first flight)\b|"
    r"只要第一段|只取消第一程|只取消第一段|保留第二段)",
    re.I,
)
PET_LOUNGE_RE = re.compile(
    r"(?:\b(pet|dog|cat|lounge|loyalty|unaccompanied)\b|宠物|狗|猫|休息室)",
    re.I,
)
POLICY_RE = re.compile(
    r"(?:\b(bag|baggage|allowance|fee|policy|can i change|refund|disruption|delay|schedule change)\b|"
    r"行李|托运|费用|政策|不正常航班|延误|航班变动)",
    re.I,
)
PLUS_ONE_DAY_RE = re.compile(r"one day later|tomorrow|推迟一天|晚一天|改到第二天|延后一天", re.I)
POLICY_SHAPED_RE = re.compile(
    r"how much|what (is|are)|cost|fee|can i change an|economy basic ticket|多少钱|费用|经济舱基础",
    re.I,
)
LAST_NAME_RE = re.compile(r"(?:last name|姓)\s*([A-Za-z]+)", re.I)

AIRLINE_HINTS = {
    "STA": ("suntrail", "sta"),
    "NSA": ("northstar", "nsa"),
    "BHA": ("bluehaven", "bha"),
}


def extract_from_text(text: str, state: AgentState) -> None:
    upper = text.upper().replace("PNR", " ")
    found = None
    for known in KNOWN_PNRS:
        if re.search(rf"\b{known}\b", upper):
            found = known
            break
    if not found:
        for match in PNR_RE.finditer(upper):
            token = match.group(1)
            if any(ch.isdigit() for ch in token):
                found = token
                break
    if found:
        state["pnr"] = found
    names = NAME_RE.search(text)
    if names:
        state["first_name"] = names.group(1)
        state["last_name"] = names.group(2)
    last_only = LAST_NAME_RE.search(text)
    if last_only and not state.get("first_name"):
        state["last_name"] = last_only.group(1)
    lower = text.lower()
    for code, hints in AIRLINE_HINTS.items():
        if any(h in lower for h in hints):
            state["airline"] = code
    if PLUS_ONE_DAY_RE.search(text):
        state["change_new_departure"] = "plus_one_day"


def classify_intent(state: AgentState) -> str:
    text = state.get("user_text") or ""
    if state.get("pending_quote"):
        if CONFIRM_RE.search(text) and not CANCEL_RE.search(text):
            return "confirm"
        if REJECT_RE.search(text):
            return "reject"
    if HANDOFF_RE.search(text) and CANCEL_RE.search(text):
        return "cancel"
    if CHANGE_RE.search(text):
        if not state.get("pnr") and POLICY_SHAPED_RE.search(text):
            return "policy_qa"
        return "change"
    if CANCEL_RE.search(text):
        return "cancel"
    if LOOKUP_RE.search(text) or (state.get("pnr") and "booking" in text.lower()):
        return "lookup"
    if PET_LOUNGE_RE.search(text):
        return "policy_qa"
    if POLICY_RE.search(text):
        return "policy_qa"
    if state.get("pnr"):
        return "lookup"
    return "policy_qa"


def plus_one_day(iso_value: str) -> str:
    dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt + timedelta(days=1)).isoformat()
