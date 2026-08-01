window.VisualizationStudio = (function () {
  let activeCharts = {};
  let currentStudioData = null;

  document.addEventListener('DOMContentLoaded', function () {
    initRevenueGoalTracker();
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

  /**
   * Renders or switches a chart dynamically.
   * @param {string} canvasId - Canvas ID
   * @param {string} chartType - 'bar', 'line', 'pie', 'doughnut', 'scatter', 'heatmap'
   * @param {object} rawData - Data payload
   */
  function renderChart(canvasId, chartType, rawData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (activeCharts[canvasId]) {
      activeCharts[canvasId].destroy();
      delete activeCharts[canvasId];
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';

    // 1. Handle Heatmap Matrix Special View
    if (chartType === 'heatmap') {
      canvas.style.display = 'none';
      let heatmapContainer = document.getElementById(canvasId + '_heatmap');
      if (!heatmapContainer) {
        heatmapContainer = document.createElement('div');
        heatmapContainer.id = canvasId + '_heatmap';
        heatmapContainer.className = 'heatmap-matrix-container';
        canvas.parentNode.appendChild(heatmapContainer);
      }
      heatmapContainer.style.display = 'block';
      renderHeatmapGrid(heatmapContainer, rawData.heatmap || rawData);
      return;
    } else {
      canvas.style.display = 'block';
      const heatmapContainer = document.getElementById(canvasId + '_heatmap');
      if (heatmapContainer) heatmapContainer.style.display = 'none';
    }

    // 2. Format datasets according to type
    let config = {
      type: chartType === 'area' ? 'line' : (chartType === 'scatter' ? 'scatter' : chartType),
      data: { labels: rawData.labels || [], datasets: [] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: ['pie', 'doughnut'].includes(chartType),
            position: 'bottom',
            labels: { color: textColor, font: { family: 'Inter', size: 12 } }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (chartType === 'scatter') {
                  const raw = ctx.raw;
                  return `${raw.name || 'Project'}: Budget $${raw.x} | Earned $${raw.y}`;
                }
                return ` ${ctx.dataset.label || 'Value'}: $${ctx.parsed.y !== undefined ? ctx.parsed.y.toLocaleString() : ctx.parsed}`;
              }
            }
          }
        },
        scales: ['pie', 'doughnut'].includes(chartType) ? {} : {
          x: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Inter' } } },
          y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Inter' } } }
        }
      }
    };

    if (chartType === 'scatter') {
      config.data.datasets = [{
        label: 'Budget vs Revenue',
        data: rawData.scatter || rawData.data || [],
        backgroundColor: '#7C3AED',
        borderColor: '#5B21B6',
        pointRadius: 6,
        pointHoverRadius: 9
      }];
    } else if (['pie', 'doughnut'].includes(chartType)) {
      config.data.datasets = [{
        data: rawData.data || (rawData.status ? Object.values(rawData.status) : []),
        backgroundColor: ['#7C3AED', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'],
        borderWidth: 0
      }];
      if (!config.data.labels.length) {
        config.data.labels = rawData.labels || (rawData.status ? Object.keys(rawData.status).map(s => s.replace('_', ' ').toUpperCase()) : []);
      }
    } else {
      config.data.datasets = [{
        label: rawData.label || 'Revenue ($)',
        data: rawData.data || [],
        backgroundColor: chartType === 'area' ? 'rgba(124, 58, 237, 0.25)' : (chartType === 'line' ? '#7C3AED' : 'rgba(124, 58, 237, 0.85)'),
        borderColor: '#7C3AED',
        borderWidth: 2,
        fill: chartType === 'area',
        tension: 0.35,
        borderRadius: chartType === 'bar' ? 6 : 0
      }];
    }

    activeCharts[canvasId] = new Chart(ctx, config);
  }

  /**
   * Renders visual Heatmap Grid for workload & activity density.
   */
  function renderHeatmapGrid(container, data) {
    const matrix = data.matrix || [];
    const days = data.days || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    let html = `<div class="heatmap-wrapper">
      <div class="heatmap-header-row">
        ${days.map(d => `<div class="heatmap-header-cell">${d}</div>`).join('')}
      </div>`;

    matrix.forEach(week => {
      html += `<div class="heatmap-week-row">`;
      week.forEach(cell => {
        const bgOpacity = Math.max(0.1, cell.intensity / 100);
        const bgColor = cell.intensity > 50 
          ? `rgba(124, 58, 237, ${bgOpacity})` 
          : `rgba(16, 185, 129, ${bgOpacity})`;
        
        html += `<div class="heatmap-cell" style="background:${bgColor};" title="${cell.date}: $${cell.val.toLocaleString()}">
          <span class="heatmap-date">${cell.date}</span>
          <span class="heatmap-val">$${cell.val > 0 ? cell.val : 0}</span>
        </div>`;
      });
      html += `</div>`;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  /**
   * Export Current Data to CSV
   */
  function exportCSV(filename, labels, data) {
    let csv = 'Label/Date,Value\n';
    labels.forEach((lbl, idx) => {
      csv += `"${lbl}",${data[idx] || 0}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'freelancetrack_report.csv';
    link.click();
  }

  return {
    renderChart: renderChart,
    exportCSV: exportCSV,
    initRevenueGoalTracker: initRevenueGoalTracker
  };
})();
