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
            pointHoverRadius: 6,
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
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: theme.secondary
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: theme.text,
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600', size: 12 },
              usePointStyle: true,
              boxWidth: 8
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 12,
            boxPadding: 6,
            usePointStyle: true,
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: '700', size: 13 }
          }
        },
        scales: {
          x: {
            grid: { color: theme.grid },
            ticks: { color: theme.text, font: { family: "'Inter', sans-serif", size: 11.5 } }
          },
          y: {
            grid: { color: theme.grid },
            ticks: {
              color: theme.text,
              font: { family: "'Inter', sans-serif", size: 11.5 },
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
            theme.secondary
          ],
          borderColor: isDark() ? '#251C2C' : '#FFFFFF',
          borderWidth: 3,
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
            labels: {
              color: theme.text,
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
              usePointStyle: true,
              padding: 16
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 10
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
          hoverBackgroundColor: '#E078A7'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 10
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: theme.text }
          },
          y: {
            grid: { color: theme.grid },
            ticks: { color: theme.text }
          }
        }
      }
    });
  };

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
