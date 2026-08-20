/**
 * FreelanceTrack — Dashboard Dynamic Manager
 * Fetches analytics and renders Chart.js charts via /api/v1/dashboard/stats/.
 *
 * Canvas IDs (must match dashboard.html):
 *   - financialTrendChart  → Monthly Revenue Line Chart
 *   - statusDistChart      → Project Status Doughnut Chart
 */

document.addEventListener('DOMContentLoaded', function () {
  // Detect dashboard page by a stat element that only exists there
  const isDashboardPage = document.getElementById('totalRevenueStat') !== null;
  if (!isDashboardPage) return;

  loadDashboardStats();
});

async function loadDashboardStats() {
  try {
    const data = await window.apiFetch('/api/v1/dashboard/stats/');

    // ── Update KPI counters ──────────────────────────────────────────────────
    updateStatElement('totalRevenueStat',   data.total_revenue,                               '₹', '');
    updateStatElement('pendingAmountStat',  data.pending_amount,                              '₹', '');
    updateStatElement('totalProjectsStat',  data.total_projects_count ?? data.active_projects_count, '', '');
    updateStatElement('totalClientsStat',   data.total_clients_count,                         '', '');
    updateStatElement('pendingTasksStat',   data.pending_tasks_count,                         '', '');

    // ── Store monthly data for chart-type switching ──────────────────────────
    window.dashboardMonthlyData = data.monthly_chart;

    // ── Render charts ────────────────────────────────────────────────────────
    renderFinancialTrendChart(data.monthly_chart);
    renderStatusDistChart(data.status_chart);

  } catch (err) {
    console.error('[Dashboard] Failed to load analytics:', err);
    renderChartsEmpty();
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function updateStatElement(elementId, value, prefix = '', suffix = '') {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.dataset.target = value;
  el.dataset.prefix = prefix;
  el.dataset.suffix = suffix;
  if (window.animateNumber) {
    window.animateNumber(el);
  } else {
    el.textContent = `${prefix}${Number(value).toLocaleString('en-IN')}${suffix}`;
  }
}

function isDarkTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark';
}

function chartColors() {
  const dark = isDarkTheme();
  return {
    primary:      dark ? '#60d9d4' : '#0f766e',
    primaryBg:    dark ? 'rgba(96,217,212,0.15)' : 'rgba(15,118,110,0.12)',
    grid:         dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
    text:         dark ? '#cbd5e1' : '#374151',
    donut: [
      dark ? '#60d9d4' : '#0d9488',   // in_progress
      dark ? '#34d399' : '#16a34a',   // completed
      dark ? '#fb923c' : '#ea580c',   // on_hold
      dark ? '#a78bfa' : '#7c3aed',   // planning
      dark ? '#94a3b8' : '#64748b',   // pending / other
    ]
  };
}

// Destroy previous Chart instance on a canvas before re-rendering
function destroyChart(canvasId) {
  const existing = Chart.getChart(canvasId);
  if (existing) existing.destroy();
}

// ── Chart: Financial Trend (Line) ──────────────────────────────────────────────

function renderFinancialTrendChart(chartData) {
  const canvas = document.getElementById('financialTrendChart');
  if (!canvas) {
    console.warn('[Dashboard] Canvas #financialTrendChart not found.');
    return;
  }

  destroyChart('financialTrendChart');
  const c = chartColors();

  const chart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: chartData?.labels || [],
      datasets: [{
        label: 'Monthly Revenue',
        data: chartData?.data || [],
        borderColor:       c.primary,
        backgroundColor:   c.primaryBg,
        borderWidth:       2.5,
        fill:              true,
        tension:           0.42,
        pointBackgroundColor: c.primary,
        pointBorderColor:     'transparent',
        pointRadius:       5,
        pointHoverRadius:  7,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDarkTheme() ? '#1e293b' : '#fff',
          borderColor:      isDarkTheme() ? '#334155' : '#e2e8f0',
          borderWidth:      1,
          titleColor:       c.text,
          bodyColor:        c.text,
          callbacks: {
            label: (ctx) => ` ₹${ctx.parsed.y.toLocaleString('en-IN', { minimumFractionDigits: 0 })}`
          }
        }
      },
      scales: {
        x: {
          grid:  { color: c.grid, drawBorder: false },
          ticks: { color: c.text, font: { family: 'Inter', size: 12 } }
        },
        y: {
          grid:  { color: c.grid, drawBorder: false },
          ticks: {
            color: c.text,
            font:  { family: 'Inter', size: 12 },
            callback: (val) => '₹' + val.toLocaleString('en-IN')
          },
          beginAtZero: true
        }
      }
    }
  });

  window.dashboardCharts = window.dashboardCharts || {};
  window.dashboardCharts.financialTrendChart = chart;
}

// ── Chart: Project Status Distribution (Doughnut) ─────────────────────────────

function renderStatusDistChart(statusData) {
  const canvas = document.getElementById('statusDistChart');
  if (!canvas) {
    console.warn('[Dashboard] Canvas #statusDistChart not found.');
    return;
  }

  destroyChart('statusDistChart');
  const c = chartColors();

  const labels = ['In Progress', 'Completed', 'On Hold', 'Planning', 'Pending'];
  const values = [
    statusData?.in_progress || 0,
    statusData?.completed   || 0,
    statusData?.on_hold     || 0,
    statusData?.planning    || 0,
    statusData?.pending     || 0,
  ];

  // If ALL zeros, show placeholder
  const total = values.reduce((a, b) => a + b, 0);
  if (total === 0) {
    values[0] = 1;
    labels[0] = 'No Data';
  }

  const chart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data:            values,
        backgroundColor: c.donut,
        borderWidth:     0,
        hoverOffset:     6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color:      c.text,
            font:       { family: 'Inter', size: 11 },
            padding:    12,
            boxWidth:   12,
            boxHeight:  12,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: isDarkTheme() ? '#1e293b' : '#fff',
          borderColor:      isDarkTheme() ? '#334155' : '#e2e8f0',
          borderWidth:      1,
          titleColor:       c.text,
          bodyColor:        c.text,
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.parsed} project${ctx.parsed !== 1 ? 's' : ''}`
          }
        }
      }
    }
  });

  window.dashboardCharts = window.dashboardCharts || {};
  window.dashboardCharts.statusDistChart = chart;
}

// ── Graceful empty state when API fails ──────────────────────────────────────

function renderChartsEmpty() {
  ['financialTrendChart', 'statusDistChart'].forEach(id => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    const parent = canvas.parentElement;
    parent.innerHTML = `
      <div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted" style="min-height:200px;">
        <i class="fas fa-chart-bar fa-2x mb-2 opacity-25"></i>
        <small>Chart data unavailable</small>
      </div>`;
  });
}

// ── Chart type switcher (used by buttons in template) ─────────────────────────

window.switchDashboardChart = function (type, btnEl) {
  if (btnEl?.parentNode) {
    btnEl.parentNode.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');
  }
  if (window.VisualizationStudio && window.dashboardMonthlyData) {
    window.VisualizationStudio.renderChart('financialTrendChart', type, window.dashboardMonthlyData);
  }
};
