/**
 * Freelancer Project Tracker — Main JavaScript
 * Handles: Dark Mode, Toast Notifications, Sidebar Toggle, Table Sorting
 */

/**
 * Helper function for internal backend API requests (/api/v1/*).
 * Enforces backend proxy rules:
 * - Directs all calls to internal /api/* endpoints
 * - Automatically injects CSRF headers and session credentials
 * - Validates responses and sanitizes errors
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function apiFetch(endpoint, options = {}) {
  // Enforce internal API route only
  if (!endpoint.startsWith('/api/')) {
    throw new Error('Security Restriction: Frontend can only communicate with internal /api/ endpoints.');
  }

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken') || '',
    'X-Requested-With': 'XMLHttpRequest'
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers
    },
    credentials: 'same-origin'
  };

  try {
    const response = await fetch(endpoint, config);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'API Error' }));
      throw new Error(errData.detail || errData.error || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    console.error('Proxy API Request Failed:', err.message);
    if (window.showToast) {
      window.showToast(err.message || 'Request failed', 'danger');
    }
    throw err;
  }
}

window.apiFetch = apiFetch;

document.addEventListener('DOMContentLoaded', function () {

  // ============================================================
  // THEME ENGINE (Light & Dark Mode)
  // ============================================================
  const htmlEl = document.documentElement;

  function getPreferredTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || savedTheme === 'light') return savedTheme;

    const legacyDark = localStorage.getItem('darkMode');
    if (legacyDark === '1') return 'dark';
    if (legacyDark === '0') return 'light';

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  function applyChartJsTheme(theme) {
    const isDark = theme === 'dark';
    const gridColor = isDark ? 'rgba(164, 240, 234, 0.15)' : 'rgba(18, 105, 98, 0.15)';
    const textColor = isDark ? '#D2F7F4' : '#003333';
    const mutedColor = isDark ? '#A4F0EA' : '#126962';

    if (window.Chart && window.Chart.instances) {
      Object.values(window.Chart.instances).forEach(chart => {
        if (chart.options.scales) {
          Object.values(chart.options.scales).forEach(scale => {
            if (scale.grid) scale.grid.color = gridColor;
            if (scale.ticks) scale.ticks.color = textColor;
          });
        }
        if (chart.options.plugins && chart.options.plugins.legend) {
          chart.options.plugins.legend.labels = {
            ...(chart.options.plugins.legend.labels || {}),
            color: textColor
          };
        }
        chart.update();
      });
    }

    if (window.dashboardCharts && Array.isArray(window.dashboardCharts)) {
      window.dashboardCharts.forEach(chart => {
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

  function setTheme(theme, save = true) {
    const isDark = theme === 'dark';
    htmlEl.setAttribute('data-theme', theme);

    if (save) {
      localStorage.setItem('theme', theme);
      localStorage.setItem('darkMode', isDark ? '1' : '0');
    }

    // Sync all toggle checkboxes on page
    document.querySelectorAll('#themeToggle, #themeToggleSettings').forEach(cb => {
      cb.checked = isDark;
    });

    // Update charts dynamically
    applyChartJsTheme(theme);

    // Dispatch event for any custom components
    document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme, isDark } }));
  }

  // Initial Theme Setup
  const currentTheme = getPreferredTheme();
  setTheme(currentTheme, false);

  // Bind Click Event to Theme Toggle Buttons
  document.addEventListener('click', function(e) {
    const btn = e.target.closest('#themeToggleBtn, #themeToggleAuthBtn, .theme-toggle-btn');
    if (btn) {
      e.preventDefault();
      const activeTheme = htmlEl.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const nextTheme = activeTheme === 'dark' ? 'light' : 'dark';
      setTheme(nextTheme, true);
    }
  });

  // Bind Change Event for traditional input switches
  document.addEventListener('change', function(e) {
    if (e.target.matches('#themeToggle, #themeToggleSettings')) {
      const nextTheme = e.target.checked ? 'dark' : 'light';
      setTheme(nextTheme, true);
    }
  });

  // Listen to OS System Color Scheme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      const savedTheme = localStorage.getItem('theme');
      const savedLegacy = localStorage.getItem('darkMode');
      if (!savedTheme && savedLegacy === null) {
        setTheme(e.matches ? 'dark' : 'light', false);
      }
    });
  }

  window.getCurrentTheme = function() {
    return htmlEl.getAttribute('data-theme') || 'light';
  };

  window.setTheme = setTheme;

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

    // C-02: Build toast using safe DOM API instead of innerHTML to prevent XSS
    const icon = document.createElement('i');
    icon.className = icons[type] || icons.info;
    icon.style.cssText = `color:${colors[type] || colors.info}; font-size:18px; flex-shrink:0;`;

    const msgSpan = document.createElement('span');
    msgSpan.style.cssText = 'flex:1; font-size:13.5px;';
    // Use textContent — never innerHTML — to prevent XSS from message content
    msgSpan.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.style.cssText = 'background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0;font-size:16px;';
    closeBtn.setAttribute('aria-label', 'Close notification');
    closeBtn.textContent = '\u00D7'; // ×
    closeBtn.addEventListener('click', () => toast.remove());

    toast.appendChild(icon);
    toast.appendChild(msgSpan);
    toast.appendChild(closeBtn);
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
  document.querySelectorAll('.progress-bar').forEach(bar => {
    const val = bar.getAttribute('aria-valuenow') || 0;
    bar.style.transition = 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    requestAnimationFrame(() => {
      bar.style.width = val + '%';
    });
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

  window.animateNumber = animateNumber;

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
  // FLOATING SPEED-DIAL (FAB) TOGGLE
  // ============================================================
  const fabWrapper = document.getElementById('fabWrapper');
  const fabToggleBtn = document.getElementById('fabToggleBtn');

  if (fabWrapper && fabToggleBtn) {
    fabToggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fabWrapper.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (fabWrapper.classList.contains('active') && !fabWrapper.contains(e.target)) {
        fabWrapper.classList.remove('active');
      }
    });
  }

  // ============================================================
  // ANIMATE PAGE CONTENT ON LOAD
  // ============================================================
  const pageContent = document.querySelector('.page-content');
  if (pageContent) {
    pageContent.style.animation = 'fadeInUp .4s ease';
  }

});
