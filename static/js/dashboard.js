/**
 * FreelanceTrack — Dashboard Dynamic Manager
 * Fetches analytics and charts through the internal backend proxy (/api/v1/dashboard/stats/).
 */

document.addEventListener('DOMContentLoaded', function () {
  const isDashboardPage = document.getElementById('totalRevenueStat') !== null;
  if (!isDashboardPage) return;

  loadDashboardStats();
});

async function loadDashboardStats() {
  try {
    // 1. Fetch filtered stats from backend proxy endpoint
    const data = await window.apiFetch('/api/v1/dashboard/stats/');

    // 2. Update KPI numbers safely
    updateStatElement('totalRevenueStat', data.total_revenue, '$', '');
    updateStatElement('pendingAmountStat', data.pending_amount, '$', '');
    updateStatElement('totalProjectsStat', data.total_projects_count ?? data.active_projects_count, '', '');
    updateStatElement('totalClientsStat', data.total_clients_count, '', '');
    updateStatElement('pendingTasksStat', data.pending_tasks_count, '', '');


    // 3. Render Chart.js charts dynamically
    window.dashboardMonthlyData = data.monthly_chart;
    renderEarningsChart(data.monthly_chart);
    renderStatusChart(data.status_chart);


  } catch (err) {
    console.error('Failed to load dashboard analytics from backend proxy:', err);
  }
}

function updateStatElement(elementId, value, prefix = '', suffix = '') {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.dataset.target = value;
  el.dataset.prefix = prefix;
  el.dataset.suffix = suffix;
  if (window.animateNumber) {
    window.animateNumber(el);
  } else {
    el.textContent = `${prefix}${value}${suffix}`;
  }
}

function renderEarningsChart(chartData) {
  const ctx = document.getElementById('earningsChart');
  if (!ctx) return;

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels || [],
      datasets: [{
        label: 'Monthly Revenue ($)',
        data: chartData.data || [],
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#4f46e5',
        pointRadius: 4,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => ` Revenue: $${context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'Inter' } }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            font: { family: 'Inter' },
            callback: (val) => '$' + val.toLocaleString()
          }
        }
      }
    }
  });

  window.dashboardCharts = window.dashboardCharts || [];
  window.dashboardCharts.push(chart);
}

function renderStatusChart(statusData) {
  const ctx = document.getElementById('statusChart');
  if (!ctx) return;

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['In Progress', 'Completed', 'On Hold', 'Planning'],
      datasets: [{
        data: [
          statusData.in_progress || 0,
          statusData.completed || 0,
          statusData.on_hold || 0,
          statusData.planning || 0
        ],
        backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#8b5cf6'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: textColor, font: { family: 'Inter', size: 12 }, padding: 16 }
        }
      },
      cutout: '72%'
    }
  });

  window.dashboardCharts = window.dashboardCharts || [];
  window.dashboardCharts.push(chart);
}

window.dashboardRawData = null;

function switchDashboardChart(type, btnEl) {
  if (btnEl && btnEl.parentNode) {
    btnEl.parentNode.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');
  }

  if (window.VisualizationStudio && window.dashboardMonthlyData) {
    window.VisualizationStudio.renderChart('earningsChart', type, window.dashboardMonthlyData);
  }
}

