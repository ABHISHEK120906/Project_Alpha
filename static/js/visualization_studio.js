/**
 * FreelanceTrack — Visualization Studio v2
 * ─────────────────────────────────────────
 * Shared chart renderer used by Reports and Analytics pages.
 * Features:
 *  • Safe chart destroy (no canvas collision errors)
 *  • Theme-aware design tokens (dark/light)
 *  • Gradient support for line/area charts
 *  • Revenue goal tracker
 *  • CSV export helper
 */

'use strict';

window.VisualizationStudio = (function () {
  const _charts = {};

  // ── Boot ─────────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    initRevenueGoalTracker();
    initAnalyticsFilters();
    if (document.getElementById('analyticsFilterForm') || document.getElementById('incomeVsExpenseChart')) {
      loadDashboardAnalytics();
    }
  });

  // ── Design Tokens ─────────────────────────────────────────────────────────────

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function getTokens() {
    const dark = isDark();
    return {
      primary:    dark ? '#f0c470' : '#c8881e',
      primaryBg:  dark ? 'rgba(240,196,112,0.20)' : 'rgba(200,136,30,0.12)',
      accent:     dark ? '#e04b2a' : '#ae2c11',
      accentBg:   dark ? 'rgba(224,75,42,0.15)' : 'rgba(174,44,17,0.08)',
      success:    dark ? '#3daa60' : '#276640',
      successBg:  dark ? 'rgba(61,170,96,0.18)' : 'rgba(39,102,64,0.10)',
      donut: dark
        ? ['#f0c470', '#3daa60', '#e04b2a', '#60a8fb', '#94a3b8', '#c084fc', '#fb923c']
        : ['#c8881e', '#276640', '#ae2c11', '#2563eb', '#64748b', '#7c3aed', '#ea580c'],
      grid:        dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
      text:        dark ? '#c8baa8' : '#3a4450',
      tick:        dark ? '#8a8070' : '#6a7480',
      tooltipBg:   dark ? '#131f2b' : '#ffffff',
      tooltipBorder: dark ? 'rgba(219,153,65,0.3)' : '#e2e8f0',
    };
  }

  // ── Safe canvas destroy ───────────────────────────────────────────────────────

  function safeDestroy(canvasId) {
    const existing = Chart.getChart(canvasId);
    if (existing) existing.destroy();
    if (_charts[canvasId]) {
      try { _charts[canvasId].destroy(); } catch (e) {}
      delete _charts[canvasId];
    }
  }

  // ── Gradient helper ───────────────────────────────────────────────────────────

  function makeGradient(ctx, colorTop, colorBottom) {
    const grad = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height || 300);
    grad.addColorStop(0, colorTop);
    grad.addColorStop(1, colorBottom);
    return grad;
  }

  // ── Main renderChart ──────────────────────────────────────────────────────────

  function renderChart(canvasId, chartType, configData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    safeDestroy(canvasId);

    const t   = getTokens();
    const ctx = canvas.getContext('2d');
    const isDoughnut = ['doughnut', 'pie'].includes(chartType);
    const isLine  = chartType === 'line';
    const isArea  = chartType === 'area';
    const resolvedType = isArea ? 'line' : chartType;
    const isFilled = isLine || isArea;

    // Build datasets
    let datasets;
    if (configData.datasets) {
      // Caller supplied full datasets array — just style them
      datasets = configData.datasets.map((ds, idx) => {
        const color = ds.borderColor || ds.backgroundColor || t.donut[idx % t.donut.length];
        if ((isLine || isArea) && !isDoughnut) {
          const grad = makeGradient(ctx, color.replace(')', ',0.25)').replace('rgb', 'rgba'), color.replace(')', ',0.02)').replace('rgb', 'rgba'));
          return {
            ...ds,
            backgroundColor: isFilled ? grad : (ds.backgroundColor || 'transparent'),
            borderWidth: ds.borderWidth ?? 2.5,
            tension: ds.tension ?? 0.42,
            pointRadius: ds.pointRadius ?? 4,
            pointHoverRadius: ds.pointHoverRadius ?? 7,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
          };
        }
        if (chartType === 'bar') {
          return { ...ds, borderRadius: 8, borderSkipped: false, barPercentage: ds.barPercentage ?? 0.7 };
        }
        return ds;
      });
    } else {
      // Simple single-dataset mode
      const color = (configData.colors || t.donut)[0] || t.primary;
      if (isDoughnut) {
        datasets = [{
          data: configData.data || [],
          backgroundColor: configData.colors || t.donut,
          borderWidth: 0,
          hoverOffset: 6,
        }];
      } else if (chartType === 'bar') {
        datasets = [{
          label: configData.label || 'Amount',
          data: configData.data || [],
          backgroundColor: t.primary + 'CC',
          hoverBackgroundColor: t.primary,
          borderRadius: 8,
          borderSkipped: false,
          barPercentage: 0.7,
        }];
      } else {
        const grad = makeGradient(ctx, t.primaryBg.replace('0.20','0.30').replace('0.12','0.22'), t.primaryBg.replace('0.20','0.02').replace('0.12','0.02'));
        datasets = [{
          label: configData.label || 'Amount',
          data: configData.data || [],
          borderColor: t.primary,
          backgroundColor: isFilled ? grad : 'transparent',
          borderWidth: 2.5,
          fill: isFilled,
          tension: 0.42,
          pointBackgroundColor: t.primary,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 7,
        }];
      }
    }

    const chartConfig = {
      type: resolvedType,
      data: {
        labels: configData.labels || [],
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: configData.horizontal ? 'y' : 'x',
        cutout: isDoughnut ? '68%' : undefined,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: isDoughnut || (configData.datasets && configData.datasets.length > 1),
            position: isDoughnut ? 'bottom' : 'top',
            align: 'end',
            labels: {
              color: t.text,
              font: { family: 'Inter', size: 11, weight: '500' },
              usePointStyle: true,
              boxHeight: 6,
              padding: 14,
            }
          },
          tooltip: {
            backgroundColor: t.tooltipBg,
            borderColor:      t.tooltipBorder,
            borderWidth:      1,
            titleColor:       t.text,
            bodyColor:        t.tick,
            padding:          12,
            cornerRadius:     10,
          }
        },
        scales: isDoughnut ? {} : {
          x: {
            grid:   { color: t.grid, drawBorder: false },
            ticks:  { color: t.tick, font: { family: 'Inter', size: 11 }, maxRotation: 0 },
            border: { color: 'transparent' },
          },
          y: {
            beginAtZero: true,
            grid:   { color: t.grid, drawBorder: false },
            ticks:  { color: t.tick, font: { family: 'Inter', size: 11 }, callback: v => '₹' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v) },
            border: { color: 'transparent' },
          }
        }
      }
    };

    _charts[canvasId] = new Chart(ctx, chartConfig);
    return _charts[canvasId];
  }

  // ── Revenue Goal Tracker ──────────────────────────────────────────────────────

  function initRevenueGoalTracker() {
    const goalCard = document.getElementById('revenueGoalCard');
    if (!goalCard) return;

    let targetGoal = parseFloat(localStorage.getItem('freelance_monthly_goal') || '5000');
    const revenueEl = document.getElementById('totalRevenueStat');
    let currentRevenue = 0;

    if (revenueEl) {
      const val = parseFloat(revenueEl.dataset.target || revenueEl.textContent.replace(/[^0-9.]/g, ''));
      if (!isNaN(val)) currentRevenue = val;
    }

    updateGoalDisplay(currentRevenue, targetGoal);

    const editBtn = document.getElementById('editGoalBtn');
    if (editBtn) {
      editBtn.addEventListener('click', function () {
        const input = prompt('Enter your monthly revenue target (₹):', targetGoal);
        if (input !== null && !isNaN(parseFloat(input))) {
          targetGoal = parseFloat(input);
          localStorage.setItem('freelance_monthly_goal', targetGoal);
          updateGoalDisplay(currentRevenue, targetGoal);
        }
      });
    }
  }

  function updateGoalDisplay(current, target) {
    const pct = Math.min(100, Math.round((current / (target || 1)) * 100));
    const pctEl  = document.getElementById('goalPercentage');
    const barEl  = document.getElementById('goalProgressBar');
    const txtEl  = document.getElementById('goalTargetText');
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;
    if (txtEl) txtEl.textContent = `₹${current.toLocaleString()} / ₹${target.toLocaleString()}`;
  }

  // ── Analytics Filter Auto-Reload ──────────────────────────────────────────────

  function initAnalyticsFilters() {
    const filterForm = document.getElementById('analyticsFilterForm');
    if (filterForm) {
      filterForm.addEventListener('change', function () {
        loadDashboardAnalytics();
      });
    }
  }

  function loadDashboardAnalytics() {
    const filterForm = document.getElementById('analyticsFilterForm');
    let query = '';
    if (filterForm) {
      query = '?' + new URLSearchParams(new FormData(filterForm)).toString();
    }

    fetch('/api/v1/dashboard/analytics/' + query, { credentials: 'same-origin' })
      .then(res => res.json())
      .then(data => {
        if (data.financial_trend) {
          renderChart('financialTrendChart', 'line', {
            labels: data.financial_trend.labels,
            datasets: [
              {
                label: 'Revenue',
                data: data.financial_trend.income,
                borderColor: isDark() ? '#f0c470' : '#c8881e',
                backgroundColor: isDark() ? 'rgba(240,196,112,0.2)' : 'rgba(200,136,30,0.12)',
                fill: true, tension: 0.42
              },
              {
                label: 'Expenses',
                data: data.financial_trend.expenses,
                borderColor: isDark() ? '#e04b2a' : '#ae2c11',
                backgroundColor: 'transparent',
                fill: false, tension: 0.42, borderDash: [6, 3]
              }
            ]
          });

          renderChart('incomeVsExpenseChart', 'bar', {
            labels: data.financial_trend.labels,
            datasets: [
              { label: 'Income', data: data.financial_trend.income, backgroundColor: isDark() ? '#f0c470CC' : '#c8881eCC', borderRadius: 8 },
              { label: 'Expenses', data: data.financial_trend.expenses, backgroundColor: isDark() ? '#e04b2aAA' : '#ae2c11AA', borderRadius: 8 }
            ]
          });
        }

        if (data.status_distribution) {
          const keys  = ['in_progress','completed','pending','on_hold','cancelled'];
          const names = ['In Progress','Completed','Pending','On Hold','Cancelled'];
          renderChart('statusDistChart', 'doughnut', {
            labels: names,
            data:   keys.map(k => data.status_distribution[k] || 0),
          });
        }

        if (data.client_revenue) {
          renderChart('clientRevenueChart', 'bar', {
            labels:     data.client_revenue.labels,
            data:       data.client_revenue.data,
            horizontal: true,
          });
        }
      })
      .catch(err => console.warn('[VisualizationStudio] Analytics load error:', err));
  }

  // ── CSV Export ────────────────────────────────────────────────────────────────

  function exportCSV(filename, labels, data) {
    let csv = 'Label,Value\n';
    labels.forEach((lbl, idx) => { csv += `"${lbl}",${data[idx] || 0}\n`; });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'analytics_report.csv';
    link.click();
  }

  // ── Public API ────────────────────────────────────────────────────────────────

  return {
    renderChart,
    exportCSV,
    loadDashboardAnalytics,
    initRevenueGoalTracker,
  };
})();
