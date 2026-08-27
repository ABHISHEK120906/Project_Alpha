/**
 * FreelanceTrack — Dashboard Analytics Engine v2
 * ─────────────────────────────────────────────────
 * Renders Chart.js 4 charts with:
 *  • Beautiful canvas gradient fills
 *  • Live dark/light theme switching (MutationObserver)
 *  • Server-side data hydration (instant load)
 *  • Async API refresh for live KPI counters
 *  • Chart type switcher: line / bar / area
 *  • Bulletproof error handling & null guards
 *
 * Canvas IDs (must match dashboard.html):
 *   financialTrendChart  →  Revenue/Expense Line/Bar/Area Chart
 *   statusDistChart      →  Project Status Doughnut Chart
 */

'use strict';

// ── Helper: Ready State Listener ───────────────────────────────────────────────

function onDocReady(fn) {
  if (document.readyState !== 'loading') {
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

// ── Design Tokens ──────────────────────────────────────────────────────────────

function isDark() {
  return document.documentElement.getAttribute('data-theme') === 'dark';
}

function getTokens() {
  const dark = isDark();
  return {
    // Financial chart
    revenueLine:   dark ? '#f0c470' : '#c8881e',
    revenueBg:     dark ? 'rgba(240,196,112,0.18)' : 'rgba(200,136,30,0.10)',
    expenseLine:   dark ? '#e04b2a' : '#ae2c11',
    expenseBg:     dark ? 'rgba(224,75,42,0.15)' : 'rgba(174,44,17,0.08)',
    // Donut palette
    donut: dark
      ? ['#f0c470', '#3daa60', '#e04b2a', '#60a8fb', '#94a3b8']
      : ['#c8881e', '#276640', '#ae2c11', '#2563eb', '#64748b'],
    // Grid & text
    grid:   dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
    text:   dark ? '#c8baa8' : '#3a4450',
    tick:   dark ? '#8a8070' : '#6a7480',
    // Tooltip
    tooltipBg:     dark ? '#131f2b' : '#ffffff',
    tooltipBorder: dark ? 'rgba(219,153,65,0.3)' : '#e2e8f0',
    tooltipTitle:  dark ? '#e5e5df' : '#1a2530',
    tooltipBody:   dark ? '#c8baa8' : '#3a4450',
  };
}

// ── Chart instance registry ────────────────────────────────────────────────────

window._dashCharts = window._dashCharts || {};

function safeDestroy(id) {
  try {
    if (typeof Chart !== 'undefined' && Chart.getChart) {
      const existing = Chart.getChart(id);
      if (existing) existing.destroy();
    }
  } catch (e) {
    console.warn('[Dashboard] Chart destroy exception for', id, e);
  }
  if (window._dashCharts[id]) {
    try { window._dashCharts[id].destroy(); } catch (e) {}
  }
  delete window._dashCharts[id];
}

// ── Canvas gradient helper ─────────────────────────────────────────────────────

function makeGradient(ctx, color1, color2) {
  try {
    const h = (ctx && ctx.canvas) ? (ctx.canvas.clientHeight || ctx.canvas.height || 260) : 260;
    const gradient = ctx.createLinearGradient(0, 0, 0, Math.max(h, 120));
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
  } catch (e) {
    return color1;
  }
}

// ── Global Chart.js defaults ───────────────────────────────────────────────────

function applyGlobalDefaults() {
  if (typeof Chart !== 'undefined' && Chart.defaults) {
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.animation.duration = 700;
    Chart.defaults.animation.easing = 'easeInOutQuart';
  }
}

// ── Boot on DOM ready ──────────────────────────────────────────────────────────

onDocReady(function () {
  applyGlobalDefaults();

  // Always render charts from server-side data first (instant)
  initChartsFromServerData();

  // Then refresh KPI counters and optionally update charts via API
  if (document.getElementById('totalRevenueStat')) {
    loadDashboardStatsAPI();
  }

  // Live theme toggle — re-render charts when user switches dark/light
  const themeObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') {
        // Small delay lets CSS vars settle before re-drawing
        setTimeout(function () {
          initChartsFromServerData();
        }, 80);
      }
    });
  });
  themeObserver.observe(document.documentElement, { attributes: true });
});

// ── Server-side chart data bootstrap ──────────────────────────────────────────

function initChartsFromServerData() {
  if (typeof Chart === 'undefined') {
    // Retry if Chart.js is still loading asynchronously
    setTimeout(initChartsFromServerData, 150);
    return;
  }

  applyGlobalDefaults();

  // Data injected by Django template into window.DASH_* globals (set in dashboard.html)
  const monthly = window.DASH_MONTHLY || { labels: [], revenue: [], income: [], expenses: [] };
  const statusD = window.DASH_STATUS  || {};

  renderFinancialChart(monthly, window._dashChartType || 'line');
  renderStatusChart(statusD);
}

// ── Chart type switcher (called by template buttons) ──────────────────────────

window.switchDashboardChart = function (type, btnEl) {
  if (btnEl && btnEl.parentNode) {
    btnEl.parentNode.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');
  }
  window._dashChartType = type;
  const monthly = window.DASH_MONTHLY || { labels: [], revenue: [], income: [], expenses: [] };
  renderFinancialChart(monthly, type);
};

// ── Async API KPI refresh ──────────────────────────────────────────────────────

async function loadDashboardStatsAPI() {
  try {
    if (!window.apiFetch) return;
    const data = await window.apiFetch('/api/v1/dashboard/stats/');
    if (!data) return;

    updateStat('totalRevenueStat',  data.total_revenue,   '₹');
    updateStat('pendingAmountStat', data.pending_amount,  '₹');
    updateStat('totalProjectsStat', data.total_projects_count ?? data.active_projects_count, '');
    updateStat('totalClientsStat',  data.total_clients_count, '');
    updateStat('pendingTasksStat',  data.pending_tasks_count, '');

    // Update global data and re-render with fresh API data
    if (data.monthly_chart) {
      window.DASH_MONTHLY = {
        labels:   data.monthly_chart.labels || [],
        revenue:  data.monthly_chart.data   || [],
        income:   data.monthly_chart.income   || data.monthly_chart.data || [],
        expenses: data.monthly_chart.expenses || [],
      };
      renderFinancialChart(window.DASH_MONTHLY, window._dashChartType || 'line');
    }
    if (data.status_chart) {
      window.DASH_STATUS = data.status_chart;
      renderStatusChart(data.status_chart);
    }
  } catch (err) {
    console.warn('[Dashboard] API refresh non-fatal error:', err.message);
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function updateStat(id, value, prefix) {
  const el = document.getElementById(id);
  if (!el) return;
  el.dataset.target = value;
  el.dataset.prefix = prefix || '';
  if (window.animateNumber) {
    window.animateNumber(el);
  } else {
    el.textContent = `${prefix || ''}${Number(value).toLocaleString('en-IN')}`;
  }
}

// ── Chart: Financial Trend ─────────────────────────────────────────────────────

function renderFinancialChart(monthly, chartType) {
  if (typeof Chart === 'undefined') return;
  const canvas = document.getElementById('financialTrendChart');
  if (!canvas) return;
  safeDestroy('financialTrendChart');

  const t = getTokens();
  const ctx = canvas.getContext('2d');

  let labels   = (monthly && monthly.labels && monthly.labels.length > 0) ? [...monthly.labels] : [];
  let revenue  = (monthly && (monthly.revenue || monthly.income)) ? [...(monthly.revenue || monthly.income)] : [];
  let expenses = (monthly && monthly.expenses) ? [...monthly.expenses] : [];

  if (labels.length === 0) {
    labels = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"];
    revenue = [0, 0, 0, 0, 0, 0];
    expenses = [0, 0, 0, 0, 0, 0];
  }

  const hasExpenses = expenses.some(v => Number(v) > 0);

  // Build gradient fills for line/area charts
  const revGrad  = makeGradient(ctx, t.revenueBg.replace('0.18', '0.35').replace('0.10','0.28'), t.revenueBg.replace('0.18','0.04').replace('0.10','0.02'));
  const expGrad  = makeGradient(ctx, t.expenseBg.replace('0.15','0.30').replace('0.08','0.22'), t.expenseBg.replace('0.15','0.04').replace('0.08','0.02'));

  const isFilled = (chartType === 'line' || chartType === 'area');
  const resolvedType = (chartType === 'area') ? 'line' : chartType;

  const datasets = [];

  if (chartType === 'bar') {
    datasets.push({
      label: 'Revenue',
      data: revenue,
      backgroundColor: t.revenueLine + 'CC',
      hoverBackgroundColor: t.revenueLine,
      borderRadius: 8,
      borderSkipped: false,
      barPercentage: 0.65,
    });
    if (hasExpenses) {
      datasets.push({
        label: 'Expenses',
        data: expenses,
        backgroundColor: t.expenseLine + 'AA',
        hoverBackgroundColor: t.expenseLine,
        borderRadius: 8,
        borderSkipped: false,
        barPercentage: 0.65,
      });
    }
  } else {
    datasets.push({
      label: 'Revenue',
      data: revenue,
      borderColor: t.revenueLine,
      backgroundColor: isFilled ? revGrad : 'transparent',
      borderWidth: 2.5,
      fill: isFilled,
      tension: 0.42,
      pointBackgroundColor: t.revenueLine,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 8,
    });
    if (hasExpenses) {
      datasets.push({
        label: 'Expenses',
        data: expenses,
        borderColor: t.expenseLine,
        backgroundColor: isFilled ? expGrad : 'transparent',
        borderWidth: 2,
        fill: isFilled,
        tension: 0.42,
        pointBackgroundColor: t.expenseLine,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 7,
        borderDash: [6, 3],
      });
    }
  }

  const chart = new Chart(canvas, {
    type: resolvedType,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: hasExpenses || datasets.length > 1,
          position: 'top',
          align: 'end',
          labels: {
            color: t.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            usePointStyle: true,
            pointStyleWidth: 12,
            boxHeight: 6,
            padding: 16,
          }
        },
        tooltip: {
          backgroundColor: t.tooltipBg,
          borderColor:      t.tooltipBorder,
          borderWidth:      1,
          titleColor:       t.tooltipTitle,
          bodyColor:        t.tooltipBody,
          padding:          12,
          cornerRadius:     10,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ₹${Number(ctx.parsed.y || 0).toLocaleString('en-IN', { minimumFractionDigits: 0 })}`
          }
        }
      },
      scales: {
        x: {
          grid:  { color: t.grid, display: true },
          ticks: { color: t.tick, font: { family: 'Inter', size: 11 }, maxRotation: 0 },
          border: { display: false },
        },
        y: {
          grid:  { color: t.grid, display: true },
          ticks: {
            color: t.tick,
            font:  { family: 'Inter', size: 11 },
            callback: (v) => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v),
          },
          border: { display: false },
          beginAtZero: true,
        }
      }
    }
  });

  window._dashCharts.financialTrendChart = chart;
}

// ── Chart: Project Status Doughnut ────────────────────────────────────────────

function renderStatusChart(statusData) {
  if (typeof Chart === 'undefined') return;
  const canvas = document.getElementById('statusDistChart');
  if (!canvas) return;
  safeDestroy('statusDistChart');
  const t = getTokens();

  const labelMap = {
    in_progress: 'In Progress',
    completed:   'Completed',
    pending:     'Pending',
    on_hold:     'On Hold',
    cancelled:   'Cancelled',
  };
  const labels = Object.keys(labelMap).map(k => labelMap[k]);
  const values = Object.keys(labelMap).map(k => Number(statusData && statusData[k] ? statusData[k] : 0));
  const total  = values.reduce((a, b) => a + b, 0);

  const hasData = total > 0;
  const displayValues = hasData ? values : [1, 0, 0, 0, 0];
  const displayLabels = hasData ? labels : ['No Projects'];

  // Center text plugin with strict boundary checking
  const centerTextPlugin = {
    id: 'centerText',
    afterDraw(chart) {
      if (!chart || !chart.chartArea) return;
      const { ctx, chartArea } = chart;
      if (!chartArea || typeof chartArea.width === 'undefined' || typeof chartArea.height === 'undefined') return;
      const { width, height, left, top } = chartArea;
      ctx.save();
      const cx = left + width / 2;
      const cy = top + height / 2;
      const num = total > 0 ? total : 0;
      ctx.font = `700 ${Math.max(12, Math.min(width, height) * 0.14)}px 'Inter', sans-serif`;
      ctx.fillStyle = t.text;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(num.toString(), cx, cy - 8);
      ctx.font = `500 ${Math.max(10, Math.min(width, height) * 0.07)}px 'Inter', sans-serif`;
      ctx.fillStyle = t.tick;
      ctx.fillText(num === 1 ? 'Project' : 'Projects', cx, cy + 12);
      ctx.restore();
    }
  };

  const chart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: hasData ? displayLabels : ['No Projects'],
      datasets: [{
        data: hasData ? displayValues : [1],
        backgroundColor: hasData ? t.donut : ['rgba(150,150,150,0.25)'],
        borderWidth: 0,
        hoverOffset: hasData ? 8 : 0,
      }]
    },
    plugins: [centerTextPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          display: hasData,
          position: 'bottom',
          labels: {
            color: t.text,
            font: { family: 'Inter', size: 11 },
            padding: 10,
            boxWidth: 10,
            boxHeight: 10,
            usePointStyle: true,
          }
        },
        tooltip: {
          enabled: hasData,
          backgroundColor: t.tooltipBg,
          borderColor:      t.tooltipBorder,
          borderWidth:      1,
          titleColor:       t.tooltipTitle,
          bodyColor:        t.tooltipBody,
          padding:          10,
          cornerRadius:     10,
          callbacks: {
            label: (ctx) => `  ${ctx.label}: ${ctx.parsed} project${ctx.parsed !== 1 ? 's' : ''}`
          }
        }
      }
    }
  });

  window._dashCharts.statusDistChart = chart;
}
