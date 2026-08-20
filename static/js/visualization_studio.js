window.VisualizationStudio = (function () {
  let activeCharts = {};

  document.addEventListener('DOMContentLoaded', function () {
    initRevenueGoalTracker();
    initAnalyticsFilters();
    // Only auto-load analytics if analytics form or specific analytics charts exist
    if (document.getElementById('analyticsFilterForm') || document.getElementById('incomeVsExpenseChart')) {
      loadDashboardAnalytics();
    }
  });

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
        const input = prompt('Enter your monthly revenue target ($):', targetGoal);
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
    const progressEl = document.getElementById('goalProgressBar');
    const targetEl = document.getElementById('goalTargetText');

    if (pctEl) pctEl.textContent = `${pct}%`;
    if (progressEl) progressEl.style.width = `${pct}%`;
    if (targetEl) targetEl.textContent = `$${current.toLocaleString()} / $${target.toLocaleString()}`;
  }

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
      const formData = new FormData(filterForm);
      query = '?' + new URLSearchParams(formData).toString();
    }

    fetch('/api/v1/dashboard/analytics/' + query)
      .then(res => res.json())
      .then(data => {
        if (data.financial_trend) {
          renderChart('financialTrendChart', 'line', {
            labels: data.financial_trend.labels,
            datasets: [
              { label: 'Revenue', data: data.financial_trend.income, borderColor: '#007F7F', backgroundColor: 'rgba(0,127,127,0.15)', fill: true, tension: 0.35 },
              { label: 'Net Profit', data: data.financial_trend.profit, borderColor: '#126962', backgroundColor: 'rgba(18,105,98,0.1)', fill: false, tension: 0.35 }
            ]
          });

          renderChart('incomeVsExpenseChart', 'bar', {
            labels: data.financial_trend.labels,
            datasets: [
              { label: 'Income ($)', data: data.financial_trend.income, backgroundColor: '#007F7F', borderRadius: 4 },
              { label: 'Expenses ($)', data: data.financial_trend.expenses, backgroundColor: '#126962', borderRadius: 4 }
            ]
          });
        }

        if (data.status_distribution) {
          const keys = Object.keys(data.status_distribution);
          const vals = Object.values(data.status_distribution);
          renderChart('statusDistChart', 'doughnut', {
            labels: keys.map(k => k.replace('_', ' ').toUpperCase()),
            data: vals,
            colors: ['#007F7F', '#126962', '#003333', '#A4F0EA', '#D2F7F4']
          });
        }

        if (data.client_revenue) {
          renderChart('clientRevenueChart', 'bar', {
            labels: data.client_revenue.labels,
            data: data.client_revenue.data,
            horizontal: true
          });
        }
      })
      .catch(err => console.log('Analytics load error:', err));
  }

  function renderChart(canvasId, chartType, configData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (activeCharts[canvasId]) {
      activeCharts[canvasId].destroy();
      delete activeCharts[canvasId];
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#D2F7F4' : '#003333';
    const gridColor = isDark ? 'rgba(164,240,234,0.15)' : 'rgba(18,105,98,0.15)';

    let chartConfig = {
      type: chartType,
      data: {
        labels: configData.labels || [],
        datasets: configData.datasets || [{
          label: configData.label || 'Amount ($)',
          data: configData.data || [],
          backgroundColor: configData.colors || (chartType === 'doughnut' ? ['#007F7F', '#126962', '#003333', '#A4F0EA', '#D2F7F4'] : '#007F7F'),
          borderColor: '#007F7F',
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: configData.horizontal ? 'y' : 'x',
        plugins: {
          legend: {
            display: ['doughnut', 'pie', 'line'].includes(chartType),
            position: 'bottom',
            labels: { color: textColor, font: { family: 'Inter', size: 12 } }
          }
        },
        scales: ['doughnut', 'pie'].includes(chartType) ? {} : {
          x: { grid: { color: gridColor }, ticks: { color: textColor } },
          y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    };

    activeCharts[canvasId] = new Chart(ctx, chartConfig);
  }

  function exportCSV(filename, labels, data) {
    let csv = 'Label,Value\n';
    labels.forEach((lbl, idx) => {
      csv += `"${lbl}",${data[idx] || 0}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'analytics_report.csv';
    link.click();
  }

  return {
    renderChart: renderChart,
    exportCSV: exportCSV,
    loadDashboardAnalytics: loadDashboardAnalytics,
    initRevenueGoalTracker: initRevenueGoalTracker
  };
})();
