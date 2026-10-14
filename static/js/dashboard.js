/*
 * Dashboard charts (Chart.js 4). Data arrives through Django's json_script tag
 * as {intake, status, revenue, medicines, age_gender, departments?, workload?}.
 *
 * Styling rules: categorical colours are assigned in a fixed slot order (never
 * cycled); bars are at most 24px thick with 4px rounded data-ends; lines are
 * 2px with ringed 8px markers; grids are hairlines; every chart has a hover
 * tooltip and a "table" toggle. Dark mode re-renders with its own palette.
 */
(() => {
  "use strict";

  const dataEl = document.getElementById("dashboard-data");
  if (!dataEl || typeof Chart === "undefined") return;
  const DATA = JSON.parse(dataEl.textContent);

  // Validated categorical palette, light and dark steps of the same hues.
  const PALETTE = {
    light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
  };

  const rwf = new Intl.NumberFormat("en-RW", { maximumFractionDigits: 0 });
  const formatRwf = (v) => `RWF ${rwf.format(v)}`;
  const compact = (v) => {
    const abs = Math.abs(v);
    if (abs >= 1e6) return `${+(v / 1e6).toFixed(1)}M`;
    if (abs >= 1e3) return `${+(v / 1e3).toFixed(1)}K`;
    return String(v);
  };

  function theme() {
    const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
    const css = getComputedStyle(document.body);
    const token = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
    return {
      dark,
      series: dark ? PALETTE.dark : PALETTE.light,
      surface: token("--bs-body-bg", dark ? "#212529" : "#ffffff"),
      text: token("--bs-secondary-color", dark ? "#c3c2b7" : "#52514e"),
      grid: dark ? "rgba(255,255,255,0.08)" : "rgba(11,11,11,0.08)",
    };
  }

  function alpha(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
  }

  function baseOptions(t, { money = false, horizontal = false, legend = false } = {}) {
    const valueAxis = {
      beginAtZero: true,
      grid: { color: t.grid, drawTicks: false },
      border: { display: false },
      ticks: { color: t.text, padding: 8, precision: 0, callback: (v) => compact(v) },
    };
    const categoryAxis = {
      grid: { display: false },
      border: { color: t.grid },
      ticks: { color: t.text, autoSkipPadding: 8 },
    };
    return {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: horizontal ? "y" : "x",
      interaction: { mode: "index", intersect: false },
      scales: horizontal ? { x: valueAxis, y: categoryAxis } : { x: categoryAxis, y: valueAxis },
      plugins: {
        legend: { display: legend, labels: { color: t.text, usePointStyle: true, boxWidth: 8, boxHeight: 8 } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = horizontal ? ctx.parsed.x : ctx.parsed.y;
              const name = ctx.dataset.label ? `${ctx.dataset.label}: ` : "";
              return name + (money ? formatRwf(v) : rwf.format(v));
            },
          },
        },
      },
    };
  }

  const bar = (label, data, color) => ({
    label,
    data,
    backgroundColor: color,
    hoverBackgroundColor: color,
    borderRadius: 4,
    borderSkipped: "start", // rounded data-end, square at the baseline
    maxBarThickness: 24,
    barPercentage: 0.85,
    categoryPercentage: 0.8,
  });

  // --- chart builders -------------------------------------------------------------------

  const builders = {
    intakeChart: (t) => ({
      type: "line",
      data: {
        labels: DATA.intake.labels,
        datasets: [{
          label: "New patients",
          data: DATA.intake.values,
          borderColor: t.series[0],
          backgroundColor: alpha(t.series[0], 0.1),
          fill: true,
          borderWidth: 2,
          tension: 0.25,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: t.series[0],
          pointBorderColor: t.surface, // 2px surface ring
          pointBorderWidth: 2,
        }],
      },
      options: baseOptions(t),
    }),

    statusChart: (t) => ({
      type: "doughnut",
      data: {
        labels: DATA.status.labels,
        datasets: [{
          label: "Appointments",
          data: DATA.status.values,
          backgroundColor: t.series.slice(0, DATA.status.values.length),
          borderColor: t.surface, // 2px surface gap between segments
          borderWidth: 2,
          hoverOffset: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { position: "bottom", labels: { color: t.text, usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 14 } },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0) || 1;
                return `${ctx.label}: ${rwf.format(ctx.parsed)} (${Math.round((100 * ctx.parsed) / total)}%)`;
              },
            },
          },
        },
      },
    }),

    departmentChart: (t) => ({
      type: "bar",
      data: { labels: DATA.departments.labels, datasets: [bar("Appointments", DATA.departments.values, t.series[0])] },
      options: baseOptions(t),
    }),

    ageGenderChart: (t) => ({
      type: "bar",
      data: {
        labels: DATA.age_gender.labels,
        datasets: [
          bar("Male", DATA.age_gender.male, t.series[0]),
          bar("Female", DATA.age_gender.female, t.series[1]),
        ],
      },
      options: baseOptions(t, { legend: true }),
    }),

    workloadChart: (t) => ({
      type: "bar",
      data: { labels: DATA.workload.labels, datasets: [bar("Completed visits", DATA.workload.values, t.series[0])] },
      options: baseOptions(t, { horizontal: true }),
    }),

    revenueChart: (t) => ({
      type: "bar",
      data: { labels: DATA.revenue.labels, datasets: [bar("Revenue", DATA.revenue.values, t.series[0])] },
      options: baseOptions(t, { money: true }),
    }),

    medicineChart: (t) => ({
      type: "bar",
      data: { labels: DATA.medicines.labels, datasets: [bar("Units prescribed", DATA.medicines.values, t.series[0])] },
      options: baseOptions(t, { horizontal: true }),
    }),
  };

  const MONEY_CHARTS = new Set(["revenueChart"]);
  const charts = {};

  function render() {
    const t = theme();
    Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = t.text;
    Object.entries(builders).forEach(([id, build]) => {
      const canvas = document.getElementById(id);
      if (!canvas) return;
      charts[id]?.destroy();
      charts[id] = new Chart(canvas, build(t));
    });
  }

  // --- table view (same numbers as the chart) ---------------------------------------------

  function buildTable(id) {
    const chart = charts[id];
    if (!chart) return "";
    const money = MONEY_CHARTS.has(id);
    const fmt = (v) => (money ? formatRwf(v) : rwf.format(v));
    const sets = chart.data.datasets;
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const head = `<tr><th></th>${sets.map((d) => `<th class="num">${esc(d.label)}</th>`).join("")}</tr>`;
    const rows = chart.data.labels
      .map((label, i) => `<tr><td>${esc(label)}</td>${sets.map((d) => `<td class="num">${fmt(d.data[i])}</td>`).join("")}</tr>`)
      .join("");
    return `<table class="table table-sm chart-table mb-0"><thead>${head}</thead><tbody>${rows}</tbody></table>`;
  }

  document.querySelectorAll("[data-chart-table]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.chartTable;
      const box = document.querySelector(`[data-chart-box="${id}"]`);
      const table = document.querySelector(`[data-table-for="${id}"]`);
      const showTable = table.classList.contains("d-none");
      if (showTable) table.innerHTML = buildTable(id);
      table.classList.toggle("d-none", !showTable);
      box.classList.toggle("d-none", showTable);
      button.setAttribute("aria-pressed", String(showTable));
      button.querySelector("i").className = showTable ? "bi bi-bar-chart" : "bi bi-table";
      button.title = showTable ? "Show as chart" : "Show as table";
    });
  });

  render();
  // Re-render with the dark/light palette whenever the colour mode changes.
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["data-bs-theme"] });
})();
