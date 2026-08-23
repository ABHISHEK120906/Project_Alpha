/**
 * Freelancer Intelligence Platform — Data Analytics Visual Engine
 * ─────────────────────────────────────────────────────────────────
 * Renders statistical distributions, histogram bins, scatter plots,
 * client revenue breakdowns, and asynchronous drill-down modals.
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
  if (!window.ANALYTICS_DATA) return;

  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  const eda = window.ANALYTICS_DATA.eda || {};
  const trends = window.ANALYTICS_DATA.trends || {};

  // Palette tokens
  const primaryColor = dark ? '#f0c470' : '#c8881e';
  const successColor = dark ? '#3daa60' : '#276640';
  const infoColor = dark ? '#60a8fb' : '#2563eb';
  const gridColor = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';
  const textColor = dark ? '#c8baa8' : '#3a4450';

  // 1. Budget Histogram Chart
  const budgetHistCtx = document.getElementById('budgetHistogramChart');
  if (budgetHistCtx && eda.budget_histogram && !eda.budget_histogram.is_empty) {
    new Chart(budgetHistCtx, {
      type: 'bar',
      data: {
        labels: eda.budget_histogram.bins,
        datasets: [{
          label: 'Project Count',
          data: eda.budget_histogram.counts,
          backgroundColor: 'rgba(219, 153, 65, 0.65)',
          borderColor: primaryColor,
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor, font: { size: 10 } } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, stepSize: 1 } }
        }
      }
    });
  }

  // 2. Payment Histogram Chart
  const paymentHistCtx = document.getElementById('paymentHistogramChart');
  if (paymentHistCtx && eda.payment_histogram && !eda.payment_histogram.is_empty) {
    new Chart(paymentHistCtx, {
      type: 'bar',
      data: {
        labels: eda.payment_histogram.bins,
        datasets: [{
          label: 'Payment Count',
          data: eda.payment_histogram.counts,
          backgroundColor: 'rgba(46, 125, 71, 0.65)',
          borderColor: successColor,
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor, font: { size: 10 } } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, stepSize: 1 } }
        }
      }
    });
  }

  // 3. Client Revenue Bivariate Chart
  const clientRevCtx = document.getElementById('clientRevenueChart');
  if (clientRevCtx && eda.client_bivariate && eda.client_bivariate.length > 0) {
    new Chart(clientRevCtx, {
      type: 'bar',
      data: {
        labels: eda.client_bivariate.map(c => c.client),
        datasets: [{
          label: 'Realized Revenue ($)',
          data: eda.client_bivariate.map(c => c.revenue),
          backgroundColor: infoColor,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor, callback: v => '$' + v.toLocaleString() } },
          y: { grid: { display: false }, ticks: { color: textColor } }
        }
      }
    });
  }

  // 4. Financial Trajectory Multi-Horizon Chart
  const trendCtx = document.getElementById('trendChart');
  if (trendCtx && trends.months) {
    new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: trends.months,
        datasets: [
          {
            label: 'Revenue ($)',
            data: trends.revenue_series,
            borderColor: primaryColor,
            backgroundColor: 'rgba(219, 153, 65, 0.15)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 4
          },
          {
            label: 'Expenses ($)',
            data: trends.expenses_series,
            borderColor: '#ef4444',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            tension: 0.35,
            pointRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: textColor, font: { size: 11 } } }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, callback: v => '$' + v.toLocaleString() } }
        }
      }
    });
  }

  // 5. Budget vs Paid Scatter Chart
  const scatterCtx = document.getElementById('scatterBudgetPaidChart');
  if (scatterCtx && eda.scatter_budget_vs_paid && eda.scatter_budget_vs_paid.length > 0) {
    new Chart(scatterCtx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Projects',
          data: eda.scatter_budget_vs_paid.map(p => ({ x: p.budget, y: p.paid, name: p.name, client: p.client })),
          backgroundColor: primaryColor,
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const raw = ctx.raw;
                return `${raw.name} (${raw.client}): Budget $${raw.x.toLocaleString()} | Paid $${raw.y.toLocaleString()}`;
              }
            }
          },
          legend: { display: false }
        },
        scales: {
          x: { title: { display: true, text: 'Budget ($)', color: textColor }, grid: { color: gridColor }, ticks: { color: textColor } },
          y: { title: { display: true, text: 'Paid Realization ($)', color: textColor }, grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    });
  }
});

// Interactive Drill-down Modal Engine
window.openDrilldownModal = function (dimension, value) {
  const modalEl = document.getElementById('drilldownModal');
  const titleEl = document.getElementById('drilldownModalLabel');
  const subEl = document.getElementById('drilldownSubtitle');
  const container = document.getElementById('drilldownTableContainer');

  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);

  titleEl.textContent = `Drill-Down: ${dimension.toUpperCase()} = "${value}"`;
  subEl.textContent = 'Querying database for granular records...';
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';
  modal.show();

  fetch(`/api/v1/analytics/drilldown/?dimension=${encodeURIComponent(dimension)}&value=${encodeURIComponent(value)}`)
    .then(r => r.json())
    .then(data => {
      subEl.textContent = `Found ${data.count || 0} matching record(s).`;
      if (!data.records || data.records.length === 0) {
        container.innerHTML = '<div class="alert alert-light text-center">No individual records found matching this segment.</div>';
        return;
      }

      let html = '<table class="table table-hover align-middle mb-0 small"><thead><tr class="table-light">';
      const keys = Object.keys(data.records[0]).filter(k => k !== 'id');
      keys.forEach(k => {
        html += `<th class="text-capitalize">${k.replace('_', ' ')}</th>`;
      });
      html += '</tr></thead><tbody>';

      data.records.forEach(row => {
        html += '<tr>';
        keys.forEach(k => {
          html += `<td>${row[k] !== undefined ? row[k] : '—'}</td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      container.innerHTML = html;
    })
    .catch(err => {
      container.innerHTML = `<div class="alert alert-danger">Failed to load drill-down data: ${err}</div>`;
    });
};
