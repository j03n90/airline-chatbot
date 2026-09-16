export type Theme = "light" | "dark";

export const THEME_KEY = "airline-ui-theme";

export const THEME_COLORS: Record<Theme, string> = {
  light: "#EDF1F7",
  dark: "#0C1018",
};

function isTheme(value: string | null): value is Theme {
  return value === "light" || value === "dark";
}

export function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (isTheme(stored)) return stored;
  } catch {
    // Ignore private-mode / blocked storage.
  }
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", THEME_COLORS[theme]);
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // Ignore private-mode / blocked storage.
  }
}

export function toggleTheme(current: Theme): Theme {
  const next: Theme = current === "light" ? "dark" : "light";
  applyTheme(next);
  return next;
}
