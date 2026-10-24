/**
 * FreelanceHub Dashboard Analytics Engine v4.0
 * Chart.js 4 visualizer supporting live theme updates,
 * Muted Petrol Teal & Botanical/Mineral tones, custom tooltips, and analytics.
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
      primary: dark ? '#8AB8AE' : '#356B68',               // Signature Muted Teal
      primaryGlow: dark ? 'rgba(138, 184, 174, 0.25)' : 'rgba(53, 107, 104, 0.20)',
      secondary: dark ? '#D6A38E' : '#C58F78',             // Soft Clay
      secondaryGlow: dark ? 'rgba(214, 163, 142, 0.20)' : 'rgba(197, 143, 120, 0.16)',
      sage: dark ? '#B4C7B4' : '#A5B9A5',                  // Muted Sage
      blue: dark ? '#96B2C8' : '#829DB5',                  // Dusty Blue
      sand: dark ? '#E2D5BE' : '#D9C9AE',                  // Warm Sand
      stone: dark ? '#929693' : '#777B78',                // Neutral Stone
      success: dark ? '#6BB892' : '#3D7D62',
      warning: dark ? '#DEAB6A' : '#B07534',
      info: dark ? '#82AEC4' : '#4A7490',
      grid: dark ? 'rgba(240, 242, 236, 0.06)' : 'rgba(37, 46, 44, 0.06)',
      text: dark ? '#B5C0B9' : '#626C68',
      tooltipBg: dark ? '#202927' : '#FFFFFF',
      tooltipBorder: dark ? '#394541' : '#E2E3DC',
      tooltipText: dark ? '#F0F2EC' : '#252E2C'
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
    const dark = isDark();

    const chartCtx = ctx.getContext('2d');
    const incomeGrad = chartCtx.createLinearGradient(0, 0, 0, 320);
    incomeGrad.addColorStop(0, dark ? 'rgba(138, 184, 174, 0.28)' : 'rgba(53, 107, 104, 0.20)');
    incomeGrad.addColorStop(1, 'rgba(53, 107, 104, 0.01)');

    const expenseGrad = chartCtx.createLinearGradient(0, 0, 0, 320);
    expenseGrad.addColorStop(0, dark ? 'rgba(214, 163, 142, 0.24)' : 'rgba(197, 143, 120, 0.18)');
    expenseGrad.addColorStop(1, 'rgba(197, 143, 120, 0.01)');

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
            tension: 0.35,
            borderWidth: 2.2,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: theme.primary,
            pointBorderColor: dark ? '#202927' : '#FFFFFF',
            pointBorderWidth: 2
          },
          {
            label: 'Disbursed / Expenses',
            data: expenseData || [8000, 11000, 9500, 17000, 14500, 21000],
            borderColor: theme.secondary,
            backgroundColor: expenseGrad,
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3.5,
            pointHoverRadius: 6,
            pointBackgroundColor: theme.secondary,
            pointBorderColor: dark ? '#202927' : '#FFFFFF',
            pointBorderWidth: 2
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
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600', size: 12 },
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 8,
              boxHeight: 8,
              padding: 20
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
            cornerRadius: 8,
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
                return '₹' + Number(val).toLocaleString();
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
    const dark = isDark();

    window._dashCharts[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels || ['Completed', 'In Progress', 'In Review', 'Open'],
        datasets: [{
          data: data || [45, 30, 15, 10],
          backgroundColor: [
            theme.primary,
            theme.sage,
            theme.secondary,
            theme.blue,
            theme.sand
          ],
          borderColor: dark ? '#202927' : '#FFFFFF',
          borderWidth: 2.5,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        layout: {
          padding: 16
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: theme.text,
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: '600' },
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 8,
              boxHeight: 8,
              padding: 18
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            titleColor: theme.tooltipText,
            bodyColor: theme.tooltipText,
            padding: 12,
            cornerRadius: 8,
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
          borderRadius: 6,
          borderSkipped: false,
          hoverBackgroundColor: theme.primaryGlow,
          barPercentage: 0.60,
          categoryPercentage: 0.70
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
            cornerRadius: 8
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
              callback: function(v) { return '₹' + Number(v).toLocaleString(); }
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
    const datasets = chart.data.datasets;

    if (type === 'area') {
      chart.config.type = 'line';
      datasets.forEach((ds) => {
        ds.fill = true;
        ds.tension = 0.35;
        ds.borderRadius = 0;
      });
    } else if (type === 'line') {
      chart.config.type = 'line';
      datasets.forEach((ds, idx) => {
        ds.fill = (idx === 0);
        ds.tension = 0.35;
        ds.borderRadius = 0;
      });
    } else if (type === 'bar') {
      chart.config.type = 'bar';
      datasets.forEach((ds) => {
        ds.fill = false;
        ds.borderRadius = 6;
        ds.barPercentage = 0.60;
        ds.categoryPercentage = 0.70;
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
