/**
 * FreelanceHub Dashboard Analytics Engine
 * State-of-the-art Chart.js 4 visualizer supporting live theme updates,
 * Baby Pink + Deep Plum gradient curves, custom tooltips, and client/freelancer/admin analytics.
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
      primary: '#DE5B88',               // Soft Rose Accent
      primaryGlow: 'rgba(222, 91, 136, 0.28)',
      primaryLight: '#F7B5CD',          // Soft Baby Pink
      secondary: '#3B142B',             // Deep Plum
      secondaryGlow: 'rgba(59, 20, 43, 0.22)',
      blush: '#FDEBF2',                 // Blush Pink
      lavender: '#ECE8F7',              // Light Lavender
      lavenderAccent: '#9884CE',
      success: '#10B981',
      warning: '#F59E0B',
      info: '#9884CE',
      grid: dark ? 'rgba(247, 181, 205, 0.08)' : 'rgba(59, 20, 43, 0.06)',
      text: dark ? '#BFAEB9' : '#756A73',
      tooltipBg: dark ? 'rgba(25, 21, 29, 0.96)' : 'rgba(255, 255, 255, 0.98)',
      tooltipBorder: dark ? 'rgba(247, 181, 205, 0.2)' : 'rgba(222, 91, 136, 0.25)',
      tooltipText: dark ? '#FDF2F6' : '#19151D'
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
    const incomeGrad = chartCtx.createLinearGradient(0, 0, 0, 320);
    incomeGrad.addColorStop(0, 'rgba(222, 91, 136, 0.35)');
    incomeGrad.addColorStop(1, 'rgba(247, 181, 205, 0.02)');

    const expenseGrad = chartCtx.createLinearGradient(0, 0, 0, 320);
    expenseGrad.addColorStop(0, 'rgba(59, 20, 43, 0.25)');
    expenseGrad.addColorStop(1, 'rgba(59, 20, 43, 0.01)');

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
          {
            label: 'Total Revenue / Income',
            data: incomeData || [12000, 19000, 15000, 28000, 24000, 34000],
            borderColor: theme.primary,
            backgroundColor: incomeGrad,
            fill: true,
            tension: 0.4,
            borderWidth: 2.5,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointBackgroundColor: theme.primary,
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 2
          },
          {
            label: 'Disbursed / Expenses',
            data: expenseData || [8000, 11000, 9500, 17000, 14500, 21000],
            borderColor: theme.secondary,
            backgroundColor: expenseGrad,
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 3.5,
            pointHoverRadius: 6,
            pointBackgroundColor: theme.secondary
          }
        ]
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
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: theme.text,
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600', size: 12.5 },
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 9,
              boxHeight: 9,
              padding: 24
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 14,
            boxPadding: 8,
            cornerRadius: 10,
            usePointStyle: true,
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: '700', size: 13 }
          }
        },
        scales: {
          x: {
            grid: { color: theme.grid, drawBorder: false },
            ticks: {
              color: theme.text,
              font: { family: "'Inter', sans-serif", size: 11.5 },
              padding: 10
            }
          },
          y: {
            beginAtZero: true,
            grid: { color: theme.grid, drawBorder: false },
            ticks: {
              color: theme.text,
              font: { family: "'Inter', sans-serif", size: 11.5 },
              padding: 12,
              callback: function (val) {
                return '$' + Number(val).toLocaleString();
              }
            }
          }
        }
      }
    });
  };

  // ── PROJECT STATUS DONUT / DISTRIBUTION ──────────────────────────────────
  window.renderProjectStatusDonut = function (canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === 'undefined') return;

    safeDestroy(canvasId);
    const theme = getChartTheme();

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels || ['Completed', 'In Progress', 'In Review', 'Open'],
        datasets: [{
          data: data || [45, 30, 15, 10],
          backgroundColor: [
            theme.success,
            theme.primary,
            theme.blush,
            theme.secondary,
            theme.lavenderAccent
          ],
          borderColor: isDark() ? '#251C2C' : '#FFFFFF',
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '66%',
        layout: {
          padding: {
            top: 16,
            bottom: 16,
            left: 16,
            right: 16
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: theme.text,
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: '600' },
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 9,
              boxHeight: 9,
              padding: 22
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 12,
            cornerRadius: 10,
            boxPadding: 6
          }
        }
      }
    });
  };

  // ── REVENUE BAR CHART ─────────────────────────────────────────────────────
  window.renderMonthlyBarChart = function (canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === 'undefined') return;

    safeDestroy(canvasId);
    const theme = getChartTheme();

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Net Volume',
          data: data || [25, 40, 32, 55, 62, 75],
          backgroundColor: theme.primary,
          borderRadius: 8,
          borderSkipped: false,
          hoverBackgroundColor: '#E078A7',
          barPercentage: 0.62,
          categoryPercentage: 0.72
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 20,
            bottom: 12,
            left: 12,
            right: 16
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 12,
            cornerRadius: 10
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: theme.text, padding: 10, font: { size: 11.5 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: theme.grid, drawBorder: false },
            ticks: {
              color: theme.text,
              padding: 12,
              font: { size: 11.5 },
              callback: function(v) { return '$' + Number(v).toLocaleString(); }
            }
          }
        }
      }
    });
  };

  // ── CHART TYPE SWITCHER HELPER ───────────────────────────────────────────
  window.switchDashboardChart = function (type, btnEl) {
    if (btnEl && btnEl.parentNode) {
      btnEl.parentNode.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btnEl.classList.add('active');
    }
    const chart = window._dashCharts['financialTrendChart'];
    if (!chart) return;
    const theme = getChartTheme();
    const datasets = chart.data.datasets;

    if (type === 'area') {
      chart.config.type = 'line';
      datasets.forEach((ds) => {
        ds.fill = true;
        ds.tension = 0.4;
        ds.borderRadius = 0;
      });
    } else if (type === 'line') {
      chart.config.type = 'line';
      datasets.forEach((ds, idx) => {
        ds.fill = (idx === 0);
        ds.tension = 0.4;
        ds.borderRadius = 0;
      });
    } else if (type === 'bar') {
      chart.config.type = 'bar';
      datasets.forEach((ds) => {
        ds.fill = false;
        ds.borderRadius = 8;
        ds.barPercentage = 0.65;
        ds.categoryPercentage = 0.72;
      });
    }
    chart.update();
  };

  // ── AUTO-INITIALIZE DASHBOARD CHARTS ──────────────────────────────────────
  function autoInitDashboard() {
    if (window.DASH_MONTHLY && document.getElementById('financialTrendChart')) {
      const labels = window.DASH_MONTHLY.labels || [];
      const income = window.DASH_MONTHLY.income || window.DASH_MONTHLY.revenue || [];
      const expense = window.DASH_MONTHLY.expenses || [];
      window.renderFinancialTrendChart('financialTrendChart', labels, income, expense);
    }
    if (window.DASH_STATUS && document.getElementById('statusDistChart')) {
      const statusObj = window.DASH_STATUS;
      const labels = Object.keys(statusObj).map(k => k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
      const data = Object.values(statusObj);
      window.renderProjectStatusDonut('statusDistChart', labels, data);
    }
  }

  if (document.readyState !== 'loading') {
    autoInitDashboard();
  } else {
    document.addEventListener('DOMContentLoaded', autoInitDashboard);
  }

  // ── LISTEN FOR THEME SWITCHING EVENTS ────────────────────────────────────
  window.addEventListener('freelancehub:themechange', function () {
    // Re-render any registered active charts
    Object.keys(window._dashCharts).forEach(function (id) {
      const chart = window._dashCharts[id];
      if (chart && typeof chart.update === 'function') {
        const theme = getChartTheme();
        if (chart.options.scales && chart.options.scales.x) {
          chart.options.scales.x.grid.color = theme.grid;
          chart.options.scales.x.ticks.color = theme.text;
        }
        if (chart.options.scales && chart.options.scales.y) {
          chart.options.scales.y.grid.color = theme.grid;
          chart.options.scales.y.ticks.color = theme.text;
        }
        chart.update();
      }
    });
  });

})();
