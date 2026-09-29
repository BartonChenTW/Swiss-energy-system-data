// Loaded in <head> so a saved light/dark choice applies before the page paints.
// No saved choice: the page follows the operating system (prefers-color-scheme).
try {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") document.documentElement.dataset.theme = saved;
} catch {}
