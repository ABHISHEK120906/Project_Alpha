/**
 * FreelanceHub Unified Frontend Core Controller
 * Handles Theme Toggling (Dark/Light), Mobile Navigation, Lucide Icons, Toasts & Modals
 */

(function () {
  'use strict';

  // ── THEME MANAGER ──────────────────────────────────────────────────────────
  const THEME_STORAGE_KEY = 'freelancehub_theme';

  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    // Broadcast event for charts and interactive components
    window.dispatchEvent(new CustomEvent('freelancehub:themechange', { detail: { theme } }));
  }

  function initTheme() {
    const currentTheme = getPreferredTheme();
    applyTheme(currentTheme);

    document.addEventListener('click', function (e) {
      const toggleBtn = e.target.closest('#themeToggleBtn, .hub-theme-toggle, [data-action="toggle-theme"]');
      if (!toggleBtn) return;
      e.preventDefault();
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  }

  // ── LUCIDE ICONS INITIALIZER ───────────────────────────────────────────────
  function initIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // ── MOBILE NAVIGATION & SIDEBAR ───────────────────────────────────────────
  function initMobileNav() {
    // Public Landing Mobile Drawer
    const drawerToggle = document.getElementById('mobileMenuToggle');
    const drawer = document.getElementById('mobileDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const drawerClose = document.getElementById('drawerClose');

    function openDrawer() {
      if (drawer) drawer.classList.add('active');
      if (drawerOverlay) drawerOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
      if (drawer) drawer.classList.remove('active');
      if (drawerOverlay) drawerOverlay.classList.remove('active');
      document.body.style.overflow = '';
    }

    if (drawerToggle) drawerToggle.addEventListener('click', openDrawer);
    if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
    if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawer);

    // Workspace Sidebars (Client, Freelancer, Admin)
    document.addEventListener('click', function (e) {
      const sidebarBtn = e.target.closest('.hub-mobile-menu-btn, #sidebarToggle, [data-toggle="sidebar"]');
      if (!sidebarBtn) return;
      e.preventDefault();

      const sidebar = document.querySelector('.hub-sidebar, .client-sidebar, .fl-sidebar, .admin-sidebar, .sidebar');
      if (sidebar) {
        sidebar.classList.toggle('open');
        let overlay = document.querySelector('.sidebar-overlay, .fh-sidebar-overlay');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.className = 'sidebar-overlay';
          document.body.appendChild(overlay);
          overlay.addEventListener('click', function () {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
          });
        }
        overlay.classList.toggle('active', sidebar.classList.contains('open'));
      }
    });
  }

  // ── AUTO-DISMISSING ALERTS ─────────────────────────────────────────────────
  function initAlerts() {
    const alerts = document.querySelectorAll('.fh-alert, .alert-dismissible');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(function () {
          if (alert.parentNode) alert.parentNode.removeChild(alert);
        }, 400);
      }, 5000);
    });
  }

  // ── CSRF HELPER FOR AJAX ───────────────────────────────────────────────────
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
  window.getCsrfToken = function () {
    return getCookie('csrftoken');
  };

  // ── BOOTSTRAP INITIALIZATION ───────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initIcons();
    initMobileNav();
    initAlerts();

    // Re-trigger icon rendering only for newly added data-lucide elements (debounced + guarded)
    var iconDebounceTimer = null;
    var iconRendering = false;
    var observer = new MutationObserver(function (mutations) {
      // Only proceed if any added node contains a data-lucide attribute
      var hasNewIcons = false;
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var node = added[j];
          if (node.nodeType === 1) {
            if (node.hasAttribute && node.hasAttribute('data-lucide')) { hasNewIcons = true; break; }
            if (node.querySelector && node.querySelector('[data-lucide]')) { hasNewIcons = true; break; }
          }
        }
        if (hasNewIcons) break;
      }
      if (!hasNewIcons || iconRendering) return;
      clearTimeout(iconDebounceTimer);
      iconDebounceTimer = setTimeout(function () {
        if (iconRendering) return;
        iconRendering = true;
        initIcons();
        iconRendering = false;
      }, 120);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });

})();
