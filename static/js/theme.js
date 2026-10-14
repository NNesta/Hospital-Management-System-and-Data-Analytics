/*
 * Colour mode (light / dark / auto), adapted from AdminLTE 4's demo script.
 * Loaded in <head> so the saved theme is applied before the page paints.
 */
(() => {
  "use strict";
  const STORAGE_KEY = "lte-theme";
  const read = () => { try { return localStorage.getItem(STORAGE_KEY); } catch { return null; } };
  const write = (theme) => { try { localStorage.setItem(STORAGE_KEY, theme); } catch { /* private mode */ } };
  const prefersDark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
  const preferred = () => read() || "auto";

  const apply = (theme) => {
    const resolved = theme === "auto" ? (prefersDark() ? "dark" : "light") : theme;
    document.documentElement.setAttribute("data-bs-theme", resolved);
  };

  const showActive = (theme) => {
    document.querySelectorAll("[data-bs-theme-value]").forEach((el) => {
      const active = el.getAttribute("data-bs-theme-value") === theme;
      el.classList.toggle("active", active);
      el.setAttribute("aria-pressed", String(active));
      el.querySelector(".bi-check-lg")?.classList.toggle("d-none", !active);
    });
    document.querySelectorAll("[data-lte-theme-icon]").forEach((icon) => {
      icon.classList.toggle("d-none", icon.dataset.lteThemeIcon !== theme);
    });
  };

  apply(preferred());

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (preferred() === "auto") apply("auto");
  });

  document.addEventListener("DOMContentLoaded", () => {
    showActive(preferred());
    document.querySelectorAll("[data-bs-theme-value]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const theme = toggle.getAttribute("data-bs-theme-value");
        write(theme);
        apply(theme);
        showActive(theme);
      });
    });
  });
})();
