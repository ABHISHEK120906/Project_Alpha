/**
 * FreelanceHub Dashboard Analytics Engine
 * State-of-the-art Chart.js 4 visualizer supporting live theme updates,
 * gradient curves, custom tooltips, and client/freelancer/admin analytics.
 */

'use strict';

(function () {
  window._dashCharts = window._dashCharts || {};

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function getChartTheme() {
    const dark = isDark();
    return {
      primary: '#7d3cff',
      primaryGlow: 'rgba(125, 60, 255, 0.25)',
      secondary: '#ff5e6c',
      accent: '#f2d53c',
      success: '#10b981',
      warning: '#f59e0b',
      info: '#3b82f6',
      grid: dark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.06)',
      text: dark ? '#94a3b8' : '#64748b',
      tooltipBg: dark ? 'rgba(15, 23, 42, 0.94)' : 'rgba(255, 255, 255, 0.96)',
      tooltipBorder: dark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(15, 23, 42, 0.12)',
      tooltipText: dark ? '#f8fafc' : '#0f172a'
    };
  }

  function safeDestroy(canvasId) {
    try {
      if (typeof Chart !== 'undefined') {
        const existing = Chart.getChart(canvasId);
        if (existing) existing.destroy();
      }
    } catch (e) {
      console.warn('[FreelanceHub] Chart destroy exception:', e);
    }
  }

  // ── CORE FINANCIAL TREND CHART (Income / Expense / Spending) ──────────────
  window.renderFinancialTrendChart = function (canvasId, labels, incomeData, expenseData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === 'undefined') return;

    safeDestroy(canvasId);
    const theme = getChartTheme();

    const chartCtx = ctx.getContext('2d');
    const incomeGrad = chartCtx.createLinearGradient(0, 0, 0, 300);
    incomeGrad.addColorStop(0, 'rgba(125, 60, 255, 0.28)');
    incomeGrad.addColorStop(1, 'rgba(125, 60, 255, 0.0)');

    const expenseGrad = chartCtx.createLinearGradient(0, 0, 0, 300);
    expenseGrad.addColorStop(0, 'rgba(255, 94, 108, 0.22)');
    expenseGrad.addColorStop(1, 'rgba(255, 94, 108, 0.0)');

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
          {
            label: 'Revenue / Inflow',
            data: incomeData || [12000, 19000, 15000, 24000, 32000, 45000],
            borderColor: '#7d3cff',
            backgroundColor: incomeGrad,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#7d3cff'
          },
          {
            label: 'Outflow / Spend',
            data: expenseData || [5000, 7500, 6000, 9500, 11000, 14000],
            borderColor: '#ff5e6c',
            backgroundColor: expenseGrad,
            borderWidth: 2,
            borderDash: [4, 4],
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: '#ff5e6c'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: { color: theme.text, font: { family: 'Plus Jakarta Sans', weight: '600', size: 12 } }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipText,
            bodyColor: theme.text,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: { color: theme.grid },
            ticks: { color: theme.text, font: { family: 'Inter', size: 11 } }
          },
          y: {
            grid: { color: theme.grid },
            ticks: {
              color: theme.text,
              font: { family: 'Inter', size: 11 },
              callback: function (val) { return '$' + val.toLocaleString(); }
            }
          }
        }
      }
    });
  };

  // ── STATUS DISTRIBUTION DOUGHNUT CHART ────────────────────────────────────
  window.renderStatusDoughnutChart = function (canvasId, labels, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === 'undefined') return;

    safeDestroy(canvasId);
    const theme = getChartTheme();

    const colors = ['#7d3cff', '#10b981', '#f59e0b', '#ff5e6c', '#64748b'];

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels || ['Active', 'Completed', 'In Review', 'Draft'],
        datasets: [{
          data: values || [12, 19, 4, 3],
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: isDark() ? '#0f172a' : '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: theme.text, font: { family: 'Plus Jakarta Sans', size: 11 }, padding: 14 }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipText,
            bodyColor: theme.text,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
          }
        }
      }
    });
  };

  // ── AUTO-INITIALIZATION FOR CANVAS HOOKS ──────────────────────────────────
  function initPageCharts() {
    if (document.getElementById('financialTrendChart')) {
      const el = document.getElementById('financialTrendChart');
      try {
        const labels = JSON.parse(el.getAttribute('data-labels') || 'null');
        const income = JSON.parse(el.getAttribute('data-income') || 'null');
        const expense = JSON.parse(el.getAttribute('data-expense') || 'null');
        window.renderFinancialTrendChart('financialTrendChart', labels, income, expense);
      } catch (e) {
        window.renderFinancialTrendChart('financialTrendChart');
      }
    }

    if (document.getElementById('statusDistChart')) {
      const el = document.getElementById('statusDistChart');
      try {
        const labels = JSON.parse(el.getAttribute('data-labels') || 'null');
        const counts = JSON.parse(el.getAttribute('data-counts') || 'null');
        window.renderStatusDoughnutChart('statusDistChart', labels, counts);
      } catch (e) {
        window.renderStatusDoughnutChart('statusDistChart');
      }
    }
  }

  // ── LISTEN FOR THEME SWITCHING EVENT ──────────────────────────────────────
  window.addEventListener('freelancehub:themechange', function () {
    setTimeout(initPageCharts, 50);
  });

  document.addEventListener('DOMContentLoaded', initPageCharts);
})();
