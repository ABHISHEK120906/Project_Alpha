/**
 * Freelancer Intelligence Platform — Data Science Visual Engine
 * ─────────────────────────────────────────────────────────────
 * Renders time-series forecast charts with uncertainty bands,
 * feature importance contributions, confusion matrix heatmaps,
 * and live interactive scenario simulators.
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
  if (!window.DATA_SCIENCE_DATA) return;

  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  const forecast = window.DATA_SCIENCE_DATA.forecast || {};
  const models = window.DATA_SCIENCE_DATA.models || {};

  // Palette tokens
  const primaryColor = dark ? '#f0c470' : '#c8881e';
  const infoColor = dark ? '#60a8fb' : '#2563eb';
  const successColor = dark ? '#3daa60' : '#276640';
  const dangerColor = dark ? '#ef4444' : '#dc2626';
  const gridColor = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';
  const textColor = dark ? '#c8baa8' : '#3a4450';

  // 1. Time-Series Revenue Forecast Chart
  const forecastCtx = document.getElementById('forecastChart');
  if (forecastCtx && forecast.is_sufficient) {
    const histLabels = forecast.historical_labels || [];
    const fcLabels = forecast.forecast_labels || [];
    const allLabels = histLabels.concat(fcLabels);

    const histData = (forecast.historical_values || []).concat(new Array(fcLabels.length).fill(null));
    
    // Connect forecast line from last historical point
    const lastHistVal = forecast.historical_values[forecast.historical_values.length - 1];
    const fcData = new Array(histLabels.length - 1).fill(null);
    fcData.push(lastHistVal);
    (forecast.forecast_values || []).forEach(v => fcData.push(v));

    const upperData = new Array(histLabels.length - 1).fill(null);
    upperData.push(lastHistVal);
    (forecast.upper_bounds || []).forEach(v => upperData.push(v));

    const lowerData = new Array(histLabels.length - 1).fill(null);
    lowerData.push(lastHistVal);
    (forecast.lower_bounds || []).forEach(v => lowerData.push(v));

    new Chart(forecastCtx, {
      type: 'line',
      data: {
        labels: allLabels,
        datasets: [
          {
            label: 'Historical Actual ($)',
            data: histData,
            borderColor: infoColor,
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            borderWidth: 2.5,
            pointRadius: 4,
            fill: false,
            tension: 0.2
          },
          {
            label: 'Estimated Forecast ($)',
            data: fcData,
            borderColor: primaryColor,
            backgroundColor: 'rgba(219, 153, 65, 0.15)',
            borderWidth: 2.5,
            borderDash: [6, 4],
            pointRadius: 5,
            pointBackgroundColor: primaryColor,
            fill: false,
            tension: 0.2
          },
          {
            label: '95% Upper Bound',
            data: upperData,
            borderColor: 'transparent',
            backgroundColor: 'rgba(219, 153, 65, 0.12)',
            pointRadius: 0,
            fill: 3,
            tension: 0.2
          },
          {
            label: '95% Lower Bound',
            data: lowerData,
            borderColor: 'transparent',
            backgroundColor: 'transparent',
            pointRadius: 0,
            fill: false,
            tension: 0.2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: textColor, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return ctx.raw !== null ? `${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString()}` : '';
              }
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor }, border: { display: false } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, callback: v => '$' + v.toLocaleString() }, border: { display: false } }
        },
        spanGaps: true
      }
    });
  }

  // 2. Feature Importance Horizontal Bar Chart
  const featCtx = document.getElementById('featureImportanceChart');
  if (featCtx && models.is_ready && models.regression_model && models.regression_model.feature_importance) {
    const featData = models.regression_model.feature_importance;
    new Chart(featCtx, {
      type: 'bar',
      data: {
        labels: featData.map(f => f.feature),
        datasets: [{
          label: 'Relative Contribution (%)',
          data: featData.map(f => f.importance_pct),
          backgroundColor: primaryColor,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor, callback: v => v + '%' }, max: 100 },
          y: { grid: { display: false }, ticks: { color: textColor } }
        }
      }
    });
  }

  // 3. Live Scenario Simulator Engine
  const simBtn = document.getElementById('btnRunScenario');
  if (simBtn) {
    simBtn.addEventListener('click', function () {
      const dur = parseFloat(document.getElementById('simDuration').value) || 30;
      const tasks = parseFloat(document.getElementById('simTasks').value) || 5;
      const budget = parseFloat(document.getElementById('simBudget').value) || 2000;

      // Model estimation calculation
      const baseProb = 0.15;
      const durFactor = Math.max(0, (dur - 45) * 0.008);
      const taskFactor = Math.max(0, (tasks - 10) * 0.025);
      const budgetFactor = (budget > 5000) ? 0.12 : 0.0;
      
      const rawProb = Math.min(0.95, Math.max(0.05, baseProb + durFactor + taskFactor + budgetFactor));
      const pct = Math.round(rawProb * 100);

      const scoreEl = document.getElementById('simRiskScore');
      const textEl = document.getElementById('simRiskText');
      const badgeEl = document.getElementById('simRiskBadge');

      if (scoreEl) scoreEl.textContent = pct + '%';
      if (textEl) {
        if (pct >= 65) {
          textEl.textContent = 'High Delay Risk: Multi-variable scope exceeds baseline delivery capacity.';
          badgeEl.className = 'badge bg-danger';
          badgeEl.textContent = 'High Risk';
        } else if (pct >= 35) {
          textEl.textContent = 'Moderate Risk: Close deadline monitoring advised.';
          badgeEl.className = 'badge bg-warning text-dark';
          badgeEl.textContent = 'Moderate';
        } else {
          textEl.textContent = 'Low Risk: Project parameters align with historically healthy deliveries.';
          badgeEl.className = 'badge bg-success';
          badgeEl.textContent = 'Healthy';
        }
      }
    });
  }
});
