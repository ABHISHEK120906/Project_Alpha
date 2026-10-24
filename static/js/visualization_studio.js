
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
 *  • Bulletproof error handling
 */

'use strict';

window.VisualizationStudio = (function () {
  const _charts = {};

  function onDocReady(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  // ── Boot ─────────────────────────────────────────────────────────────────────

  onDocReady(function () {
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
      primary: dark ? '#8AB8AE' : '#356B68',
      primaryBg: dark ? 'rgba(138,184,174,0.20)' : 'rgba(53,107,104,0.12)',
      accent: dark ? '#D6A38E' : '#C58F78',
      accentBg: dark ? 'rgba(214,163,142,0.15)' : 'rgba(197,143,120,0.10)',
      success: dark ? '#6BB892' : '#3D7D62',
      successBg: dark ? 'rgba(107,184,146,0.18)' : 'rgba(61,125,98,0.10)',
      donut: dark
        ? ['#8AB8AE', '#6BB892', '#D6A38E', '#96B2C8', '#E2D5BE', '#929693', '#B4C7B4']
        : ['#356B68', '#3D7D62', '#C58F78', '#829DB5', '#D9C9AE', '#777B78', '#A5B9A5'],
      grid: dark ? 'rgba(240,242,236,0.06)' : 'rgba(37,46,44,0.06)',
      text: dark ? '#B5C0B9' : '#626C68',
      tick: dark ? '#808D86' : '#777B78',
      tooltipBg: dark ? '#202927' : '#FFFFFF',
      tooltipBorder: dark ? '#394541' : '#E2E3DC',
    };
  }

  // ── Safe canvas destroy ───────────────────────────────────────────────────────

  function safeDestroy(canvasId) {
    try {
      if (typeof Chart !== 'undefined' && Chart.getChart) {
        const existing = Chart.getChart(canvasId);
        if (existing) existing.destroy();
      }
    } catch (e) { }
    if (_charts[canvasId]) {
      try { _charts[canvasId].destroy(); } catch (e) { }
      delete _charts[canvasId];
    }
  }

  // ── Gradient helper ───────────────────────────────────────────────────────────

  function makeGradient(ctx, colorTop, colorBottom) {
    try {
      const h = (ctx && ctx.canvas) ? (ctx.canvas.clientHeight || ctx.canvas.height || 300) : 300;
      const grad = ctx.createLinearGradient(0, 0, 0, Math.max(h, 120));
      grad.addColorStop(0, colorTop);
      grad.addColorStop(1, colorBottom);
      return grad;
    } catch (e) {
      return colorTop;
    }
  }

  // ── Main renderChart ──────────────────────────────────────────────────────────

  function renderChart(canvasId, chartType, configData) {
    if (typeof Chart === 'undefined') {
      setTimeout(function () { renderChart(canvasId, chartType, configData); }, 150);
      return;
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    safeDestroy(canvasId);

    const t = getTokens();
    const ctx = canvas.getContext('2d');
    const isDoughnut = ['doughnut', 'pie'].includes(chartType);
    const isLine = chartType === 'line';
    const isArea = chartType === 'area';
    const resolvedType = isArea ? 'line' : chartType;
    const isFilled = isLine || isArea;

    configData = configData || {};

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
      const dataVals = configData.data || [];
      if (isDoughnut) {
        datasets = [{
          data: dataVals.length > 0 ? dataVals : [1],
          backgroundColor: dataVals.length > 0 ? (configData.colors || t.donut) : ['rgba(150,150,150,0.25)'],
          borderWidth: 0,
          hoverOffset: dataVals.length > 0 ? 6 : 0,
        }];
      } else if (chartType === 'bar') {
        datasets = [{
          label: configData.label || 'Amount',
          data: dataVals,
          backgroundColor: t.primary + 'CC',
          hoverBackgroundColor: t.primary,
          borderRadius: 8,
          borderSkipped: false,
          barPercentage: 0.7,
        }];
      } else {
        const grad = makeGradient(ctx, t.primaryBg.replace('0.20', '0.30').replace('0.12', '0.22'), t.primaryBg.replace('0.20', '0.02').replace('0.12', '0.02'));
        datasets = [{
          label: configData.label || 'Amount',
          data: dataVals,
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
        layout: {
          padding: {
            top: 20,
            bottom: 12,
            left: 14,
            right: 18
          }
        },
        indexAxis: configData.horizontal ? 'y' : 'x',
        cutout: isDoughnut ? '66%' : undefined,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: isDoughnut || (configData.datasets && configData.datasets.length > 1),
            position: isDoughnut ? 'bottom' : 'top',
            align: 'end',
            labels: {
              color: t.text,
              font: { family: 'Inter', size: 12, weight: '500' },
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 9,
              boxHeight: 9,
              padding: 20,
            }
          },
          tooltip: {
            backgroundColor: t.tooltipBg,
            borderColor: t.tooltipBorder,
            borderWidth: 1,
            titleColor: t.text,
            bodyColor: t.tick,
            padding: 12,
            cornerRadius: 10,
            callbacks: {
              label: function (c) {
                const val = c.parsed && typeof c.parsed.y !== 'undefined' ? c.parsed.y : (c.parsed && typeof c.parsed.x !== 'undefined' ? c.parsed.x : c.raw);
                return ` ${c.dataset.label || ''}: ₹${Number(val || 0).toLocaleString('en-IN')}`;
              }
            }
          }
        },
        scales: isDoughnut ? {} : {
          x: {
            grid: { color: t.grid, drawBorder: false },
            ticks: { color: t.tick, font: { family: 'Inter', size: 11.5 }, maxRotation: 0, padding: 10 },
            border: { color: 'transparent' },
          },
          y: {
            beginAtZero: true,
            grid: { color: t.grid, drawBorder: false },
            ticks: { color: t.tick, font: { family: 'Inter', size: 11.5 }, padding: 12, callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v) },
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
    const pctEl = document.getElementById('goalPercentage');
    const barEl = document.getElementById('goalProgressBar');
    const txtEl = document.getElementById('goalTargetText');
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
      .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
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
          const keys = ['in_progress', 'completed', 'pending', 'on_hold', 'cancelled'];
          const names = ['In Progress', 'Completed', 'Pending', 'On Hold', 'Cancelled'];
          renderChart('statusDistChart', 'doughnut', {
            labels: names,
            data: keys.map(k => data.status_distribution[k] || 0),
          });
        }

        if (data.client_revenue) {
          renderChart('clientRevenueChart', 'bar', {
            labels: data.client_revenue.labels,
            data: data.client_revenue.data,
            horizontal: true,
          });
        }
      })
      .catch(err => console.warn('[VisualizationStudio] Analytics load error:', err));
  }

  // ── CSV Export ────────────────────────────────────────────────────────────────

  function exportCSV(filename, labels, data) {
    labels = labels || [];
    data = data || [];
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
