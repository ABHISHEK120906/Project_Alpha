/**
 * FreelanceTrack — Dashboard Analytics Engine v2
 * ─────────────────────────────────────────────────
 * Renders Chart.js 4 charts with:
 *  • Beautiful canvas gradient fills
 *  • Live dark/light theme switching (MutationObserver)
 *  • Server-side data hydration (instant load)
 *  • Async API refresh for live KPI counters
 *  • Chart type switcher: line / bar / area
 *
 * Canvas IDs (must match dashboard.html):
 *   financialTrendChart  →  Revenue/Expense Line/Bar/Area Chart
 *   statusDistChart      →  Project Status Doughnut Chart
 */

'use strict';

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
  const existing = Chart.getChart(id);
  if (existing) existing.destroy();
  if (window._dashCharts[id]) { try { window._dashCharts[id].destroy(); } catch(e){} }
  delete window._dashCharts[id];
}

// ── Canvas gradient helper ─────────────────────────────────────────────────────

function makeGradient(ctx, color1, color2) {
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height || 260);
  gradient.addColorStop(0, color1);
  gradient.addColorStop(1, color2);
  return gradient;
}

// ── Global Chart.js defaults (applied once) ────────────────────────────────────

Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.animation.duration = 700;
Chart.defaults.animation.easing = 'easeInOutQuart';

// ── Boot on DOM ready ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
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
  // Data injected by Django template into window.DASH_* globals (set in dashboard.html)
  const monthly  = window.DASH_MONTHLY  || { labels: [], revenue: [], income: [], expenses: [] };
  const statusD  = window.DASH_STATUS   || {};

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
    const data = await window.apiFetch('/api/v1/dashboard/stats/');

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
    console.warn('[Dashboard] API refresh failed, keeping server-rendered charts:', err.message);
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
  const canvas = document.getElementById('financialTrendChart');
  if (!canvas) return;
  safeDestroy('financialTrendChart');
  const t = getTokens();
  const ctx = canvas.getContext('2d');

  const labels   = monthly.labels   || [];
  const revenue  = monthly.revenue  || monthly.income || [];
  const expenses = monthly.expenses || [];

  const hasExpenses = expenses.some(v => v > 0);

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
          display: hasExpenses,
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
            label: (ctx) => ` ${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN', { minimumFractionDigits: 0 })}`
          }
        }
      },
      scales: {
        x: {
          grid:  { color: t.grid, drawBorder: false },
          ticks: { color: t.tick, font: { family: 'Inter', size: 11 }, maxRotation: 0 },
          border: { color: 'transparent' },
        },
        y: {
          grid:  { color: t.grid, drawBorder: false },
          ticks: {
            color: t.tick,
            font:  { family: 'Inter', size: 11 },
            callback: (v) => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v),
          },
          border: { color: 'transparent' },
          beginAtZero: true,
        }
      }
    }
  });

  window._dashCharts.financialTrendChart = chart;
}

// ── Chart: Project Status Doughnut ────────────────────────────────────────────

function renderStatusChart(statusData) {
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
  const values = Object.keys(labelMap).map(k => (statusData[k] || 0));
  const total  = values.reduce((a, b) => a + b, 0);

  // If no data, show placeholder
  const displayValues = total > 0 ? values : [1, 0, 0, 0, 0];
  const displayLabels = total > 0 ? labels : ['No Data'];

  // Center text plugin
  const centerTextPlugin = {
    id: 'centerText',
    afterDraw(chart) {
      const { ctx, chartArea: { width, height, left, top } } = chart;
      ctx.save();
      const cx = left + width / 2;
      const cy = top + height / 2;
      const num = total > 0 ? total : 0;
      ctx.font = `700 ${Math.min(width, height) * 0.14}px Inter, sans-serif`;
      ctx.fillStyle = t.text;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(num.toString(), cx, cy - 8);
      ctx.font = `400 ${Math.min(width, height) * 0.07}px Inter, sans-serif`;
      ctx.fillStyle = t.tick;
      ctx.fillText('Projects', cx, cy + 12);
      ctx.restore();
    }
  };

  const chart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: displayLabels,
      datasets: [{
        data: displayValues,
        backgroundColor: t.donut,
        borderWidth: 0,
        hoverOffset: 8,
      }]
    },
    plugins: [centerTextPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
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

// ── Graceful empty state ───────────────────────────────────────────────────────

function renderChartsEmpty() {
  ['financialTrendChart', 'statusDistChart'].forEach(id => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    canvas.parentElement.innerHTML = `
      <div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted" style="min-height:200px;gap:8px;">
        <i class="fas fa-chart-bar fa-2x opacity-25"></i>
        <small style="font-size:0.78rem;">Chart data unavailable</small>
      </div>`;
  });
}
