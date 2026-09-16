import { ReactNode, useEffect, useRef } from "react";

type Props = {
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export default function LabDrawer({ open, onToggle, children }: Props) {
  const doneRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onToggle();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onToggle]);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement;
    if (previous instanceof HTMLElement) previous.blur();
    doneRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const lab = document.getElementById("mock-lab");
    const handle = document.querySelector(".lab-handle");
    const active = document.activeElement;
    if (
      active instanceof Node &&
      !lab?.contains(active) &&
      !handle?.contains(active)
    ) {
      doneRef.current?.focus();
    }
  }, [open, children]);

  return (
    <>
      <button
        type="button"
        className={`lab-handle glass ${open ? "open" : ""}`}
        onClick={onToggle}
        aria-expanded={open}
        aria-controls="mock-lab"
        title={open ? "Hide Mock lab" : "Show Mock lab"}
      >
        <span className="handle-bar" />
        <span className="handle-label">Lab</span>
      </button>
      {open ? <button type="button" className="lab-backdrop" aria-label="Close Mock lab" onClick={onToggle} /> : null}
      <aside
        id="mock-lab"
        className={`lab-drawer ${open ? "open" : ""}`}
        aria-hidden={!open}
        aria-modal={open}
        role={open ? "dialog" : undefined}
        aria-labelledby="mock-lab-title"
      >
        <div className="lab-sheet glass">
          <header className="lab-header">
            <div>
              <p className="lab-kicker">Inspector</p>
              <h2 id="mock-lab-title">Mock Lab</h2>
            </div>
            <button type="button" className="done-btn" ref={doneRef} onClick={onToggle}>
              Done
            </button>
          </header>
          <div className="lab-body">{children}</div>
        </div>
      </aside>
    </>
  );
}
