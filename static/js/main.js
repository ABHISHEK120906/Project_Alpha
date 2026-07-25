/**
 * Freelancer Project Tracker — Main JavaScript
 * Handles: Dark Mode, Toast Notifications, Sidebar Toggle, Table Sorting
 */

document.addEventListener('DOMContentLoaded', function () {

  // ============================================================
  // DARK MODE
  // ============================================================
  const themeToggle = document.getElementById('themeToggle');
  const htmlEl = document.documentElement;

  function applyTheme(dark) {
    htmlEl.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (themeToggle) themeToggle.checked = dark;
    localStorage.setItem('darkMode', dark ? '1' : '0');
    // Update Chart.js charts if they exist
    if (window.dashboardCharts) {
      window.dashboardCharts.forEach(chart => {
        const gridColor = dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
        const textColor = dark ? '#94a3b8' : '#64748b';
        if (chart.options.scales) {
          Object.values(chart.options.scales).forEach(scale => {
            if (scale.grid) scale.grid.color = gridColor;
            if (scale.ticks) scale.ticks.color = textColor;
          });
        }
        if (chart.options.plugins && chart.options.plugins.legend) {
          chart.options.plugins.legend.labels = { color: textColor };
        }
        chart.update();
      });
    }
  }

  const savedDark = localStorage.getItem('darkMode');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(savedDark !== null ? savedDark === '1' : prefersDark);

  if (themeToggle) {
    themeToggle.addEventListener('change', () => applyTheme(themeToggle.checked));
  }

  // ============================================================
  // SIDEBAR TOGGLE (Mobile)
  // ============================================================
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('mainSidebar');
  const overlay = document.getElementById('sidebarOverlay');

  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    overlay && overlay.classList.remove('d-block');
    document.body.style.overflow = '';
  }

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      const isOpen = sidebar.classList.contains('open');
      if (overlay) overlay.classList.toggle('d-block', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });
  }

  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // ============================================================
  // TOAST NOTIFICATIONS (from Django messages)
  // ============================================================
  function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
      success: 'fas fa-check-circle',
      error:   'fas fa-times-circle',
      danger:  'fas fa-times-circle',
      warning: 'fas fa-exclamation-triangle',
      info:    'fas fa-info-circle',
    };

    const colors = {
      success: '#10b981',
      error:   '#ef4444',
      danger:  '#ef4444',
      warning: '#f59e0b',
      info:    '#3b82f6',
    };

    const toast = document.createElement('div');
    const resolvedType = type === 'danger' ? 'error' : type;
    toast.className = `custom-toast ${resolvedType}`;
    toast.innerHTML = `
      <i class="${icons[type] || icons.info}" style="color:${colors[type] || colors.info}; font-size:18px; flex-shrink:0;"></i>
      <span style="flex:1; font-size:13.5px;">${message}</span>
      <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0;font-size:16px;">&times;</button>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('hiding');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // Trigger toasts for existing Django messages rendered in DOM
  document.querySelectorAll('[data-toast]').forEach(el => {
    showToast(el.dataset.toast, el.dataset.toastType || 'info');
    el.remove();
  });

  // Make showToast globally available
  window.showToast = showToast;

  // ============================================================
  // AUTO-DISMISS ALERTS
  // ============================================================
  setTimeout(() => {
    document.querySelectorAll('.auto-dismiss').forEach(el => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    });
  }, 5000);

  // ============================================================
  // CONFIRM DELETE
  // ============================================================
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      const msg = this.dataset.confirm || 'Are you sure you want to delete this? This action cannot be undone.';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ============================================================
  // PROGRESS BAR ANIMATIONS
  // ============================================================
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        const val = bar.getAttribute('aria-valuenow');
        bar.style.width = val + '%';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.progress-bar').forEach(bar => {
    const val = bar.getAttribute('aria-valuenow') || 0;
    bar.style.width = '0%';
    bar.style.transition = 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    observer.observe(bar);
  });

  // ============================================================
  // SEARCH INPUT DEBOUNCE
  // ============================================================
  const searchInputs = document.querySelectorAll('.live-search');
  searchInputs.forEach(input => {
    let timeout;
    input.addEventListener('input', () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        input.closest('form').submit();
      }, 400);
    });
  });

  // ============================================================
  // ANIMATE STAT NUMBERS
  // ============================================================
  function animateNumber(el) {
    const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ''));
    if (isNaN(target)) return;
    const isDecimal = String(target).includes('.');
    const duration = 800;
    const start = performance.now();
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = target * ease;
      el.textContent = prefix + (isDecimal ? current.toFixed(2) : Math.round(current).toLocaleString()) + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  const numObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateNumber(entry.target);
        numObserver.unobserve(entry.target);
      }
    });
  });

  document.querySelectorAll('.stat-number').forEach(el => numObserver.observe(el));

  // ============================================================
  // TABLE ROW CLICK NAVIGATION
  // ============================================================
  document.querySelectorAll('tr[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      if (!e.target.closest('a, button, input, select')) {
        window.location.href = this.dataset.href;
      }
    });
  });

  // ============================================================
  // ANIMATE PAGE CONTENT ON LOAD
  // ============================================================
  const pageContent = document.querySelector('.page-content');
  if (pageContent) {
    pageContent.style.animation = 'fadeInUp .4s ease';
  }

});
