/**
 * ==========================================================================
 * FREELANCEHUB — 3D INTERACTIVE ENGINE v1.0
 * Pure Vanilla JavaScript (Zero External Dependencies)
 * Features:
 *   1. 3D Rotating Polyhedron & Ambient Particle Canvas
 *   2. 60fps GPU 3D Card Tilt & Dynamic Specular Glare Physics
 *   3. Floating 3D Orbital Chips Parallax
 * ==========================================================================
 */

(function () {
  'use strict';

  // Check user preference for reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ==========================================================================
     1. 3D ROTATING POLYHEDRON & PARTICLE CANVAS
     ========================================================================== */
  function initHero3DCanvas() {
    const canvas = document.getElementById('hero3dCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width, height, cx, cy;
    let animId;
    let mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };

    // Resize canvas to match display size
    function resize() {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      cx = width * 0.72; // Position 3D core behind right hero visual
      cy = height * 0.48;
    }

    resize();
    window.addEventListener('resize', resize, { passive: true });

    // Track mouse over hero section for 3D tilt reaction
    const heroSection = document.querySelector('.fhp-hero');
    if (heroSection) {
      heroSection.addEventListener('mousemove', function (e) {
        const rect = heroSection.getBoundingClientRect();
        mouse.targetX = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
        mouse.targetY = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
      }, { passive: true });

      heroSection.addEventListener('mouseleave', function () {
        mouse.targetX = 0;
        mouse.targetY = 0;
      });
    }

    // 3D Icosahedron vertices definition (Golden Ratio φ)
    const phi = (1 + Math.sqrt(5)) / 2;
    const baseRadius = Math.min(width, height) * 0.32;

    const rawVertices = [
      [-1,  phi, 0], [ 1,  phi, 0], [-1, -phi, 0], [ 1, -phi, 0],
      [ 0, -1,  phi], [ 0,  1,  phi], [ 0, -1, -phi], [ 0,  1, -phi],
      [ phi, 0, -1], [ phi, 0,  1], [-phi, 0, -1], [-phi, 0,  1]
    ];

    // Normalize and scale vertices
    const vertices = rawVertices.map(v => {
      const len = Math.hypot(v[0], v[1], v[2]);
      return { x: (v[0] / len), y: (v[1] / len), z: (v[2] / len) };
    });

    // Edges connecting vertices of icosahedron
    const edges = [];
    for (let i = 0; i < vertices.length; i++) {
      for (let j = i + 1; j < vertices.length; j++) {
        const dx = vertices[i].x - vertices[j].x;
        const dy = vertices[i].y - vertices[j].y;
        const dz = vertices[i].z - vertices[j].z;
        const dist = Math.hypot(dx, dy, dz);
        // In a regular icosahedron, distance between adjacent vertices is ~1.05
        if (dist > 0.95 && dist < 1.15) {
          edges.push([i, j]);
        }
      }
    }

    // 3D Floating Dust Particles
    const PARTICLE_COUNT = 36;
    const particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: (Math.random() - 0.5) * 600,
        y: (Math.random() - 0.5) * 500,
        z: (Math.random() - 0.5) * 400,
        size: Math.random() * 2 + 1,
        speed: Math.random() * 0.003 + 0.001,
        orbitRad: Math.random() * 180 + 120,
        angle: Math.random() * Math.PI * 2
      });
    }

    // Rotation angles
    let rotX = 0.35;
    let rotY = 0.45;
    let rotZ = 0.15;

    function render() {
      ctx.clearRect(0, 0, width, height);

      const isDark = document.documentElement.getAttribute('data-theme') !== 'light';

      // Colors based on theme
      const primaryColor = isDark ? '234, 170, 100' : '60, 55, 54'; // Amber Gold vs Charcoal
      const cyanAccent   = isDark ? '96, 212, 230'  : '56, 178, 172';
      const blushAccent  = isDark ? '249, 213, 213' : '224, 112, 112';

      // Smooth mouse follow interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      // Update rotation
      if (!prefersReducedMotion) {
        rotX += 0.0028 + mouse.y * 0.008;
        rotY += 0.0036 + mouse.x * 0.008;
        rotZ += 0.0012;
      }

      const rad = Math.min(width, height) * 0.28;
      const fov = 500;

      // Precalculate trig values
      const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
      const cosZ = Math.cos(rotZ), sinZ = Math.sin(rotZ);

      // Transform 3D vertices
      const projected = vertices.map(v => {
        // Rotate around Y
        let x1 = v.x * cosY + v.z * sinY;
        let y1 = v.y;
        let z1 = -v.x * sinY + v.z * cosY;

        // Rotate around X
        let x2 = x1;
        let y2 = y1 * cosX - z1 * sinX;
        let z2 = y1 * sinX + z1 * cosX;

        // Rotate around Z
        let x3 = x2 * cosZ - y2 * sinZ;
        let y3 = x2 * sinZ + y2 * cosZ;
        let z3 = z2;

        const scale = rad;
        const px = x3 * scale;
        const py = y3 * scale;
        const pz = z3 * scale;

        // Perspective projection
        const depth = pz + fov;
        const factor = fov / (depth > 1 ? depth : 1);
        return {
          x: cx + px * factor,
          y: cy + py * factor,
          z: pz,
          factor: factor
        };
      });

      // 1. Draw glowing ambient halo behind the core
      const glowGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad * 1.5);
      glowGrad.addColorStop(0, `rgba(${primaryColor}, ${isDark ? '0.12' : '0.06'})`);
      glowGrad.addColorStop(0.5, `rgba(${cyanAccent}, ${isDark ? '0.06' : '0.03'})`);
      glowGrad.addColorStop(1, 'transparent');
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, rad * 1.6, 0, Math.PI * 2);
      ctx.fill();

      // 2. Draw 3D Edges
      edges.forEach(([i, j]) => {
        const p1 = projected[i];
        const p2 = projected[j];
        const avgZ = (p1.z + p2.z) / 2;
        const alpha = Math.max(0.12, Math.min(0.85, (avgZ + rad) / (2 * rad)));

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);

        const edgeGrad = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
        edgeGrad.addColorStop(0, `rgba(${primaryColor}, ${alpha * 0.9})`);
        edgeGrad.addColorStop(0.5, `rgba(${cyanAccent}, ${alpha * 0.7})`);
        edgeGrad.addColorStop(1, `rgba(${blushAccent}, ${alpha * 0.85})`);

        ctx.strokeStyle = edgeGrad;
        ctx.lineWidth = Math.max(1, 1.8 * ((p1.factor + p2.factor) / 2));
        ctx.stroke();
      });

      // 3. Draw 3D Vertices (Glowing Nodes)
      projected.forEach(p => {
        const alpha = Math.max(0.2, Math.min(0.95, (p.z + rad) / (2 * rad)));
        const nodeRadius = Math.max(2, 4 * p.factor);

        // Node Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, nodeRadius * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${primaryColor}, ${alpha * 0.3})`;
        ctx.fill();

        // Node Core
        ctx.beginPath();
        ctx.arc(p.x, p.y, nodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = isDark ? `rgba(255, 255, 255, ${alpha})` : `rgba(${primaryColor}, ${alpha})`;
        ctx.fill();
      });

      // 4. Draw Floating Orbital Star Particles
      particles.forEach(pt => {
        pt.angle += pt.speed;
        const px = Math.cos(pt.angle) * pt.orbitRad;
        const pz = Math.sin(pt.angle) * pt.orbitRad;
        const py = pt.y + Math.sin(pt.angle * 2) * 20;

        // Rotate particles slightly with hero tilt
        const xRot = px * cosY + pz * sinY;
        const zRot = -px * sinY + pz * cosY;

        const depth = zRot + fov;
        const factor = fov / (depth > 1 ? depth : 1);
        const screenX = cx + xRot * factor;
        const screenY = cy + py * factor;
        const pAlpha = Math.max(0.15, Math.min(0.75, (zRot + 200) / 400));

        ctx.beginPath();
        ctx.arc(screenX, screenY, pt.size * factor, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${primaryColor}, ${pAlpha})`;
        ctx.fill();
      });

      animId = requestAnimationFrame(render);
    }

    render();
  }

  /* ==========================================================================
     2. 60FPS GPU 3D CARD TILT & SPECULAR GLARE PHYSICS
     ========================================================================== */
  function init3DTiltCards() {
    if (prefersReducedMotion) return;

    const cards = document.querySelectorAll('[data-tilt-3d], .fhp-3d-card, .fhp-design-card');
    if (!cards.length) return;

    cards.forEach(card => {
      // Create glare overlay element if not present
      let glare = card.querySelector('.fhp-card-glare');
      if (!glare) {
        glare = document.createElement('div');
        glare.className = 'fhp-card-glare';
        card.appendChild(glare);
      }

      let isHovered = false;
      let frameId = null;
      let currentX = 0, currentY = 0;
      let targetX = 0, targetY = 0;
      let glareX = 50, glareY = 50;

      // Max tilt angle
      const MAX_TILT = parseFloat(card.getAttribute('data-max-tilt')) || 12;

      function updateTilt() {
        if (!isHovered) {
          // Smooth return to center
          currentX += (0 - currentX) * 0.15;
          currentY += (0 - currentY) * 0.15;

          if (Math.abs(currentX) < 0.05 && Math.abs(currentY) < 0.05) {
            currentX = 0;
            currentY = 0;
            card.style.transform = 'perspective(1200px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
            cancelAnimationFrame(frameId);
            frameId = null;
            return;
          }
        } else {
          // Smooth follow to target
          currentX += (targetX - currentX) * 0.18;
          currentY += (targetY - currentY) * 0.18;
        }

        const rotateX = (-currentY * MAX_TILT).toFixed(2);
        const rotateY = (currentX * MAX_TILT).toFixed(2);
        const scale = isHovered ? 1.025 : 1;

        card.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(${scale}, ${scale}, ${scale})`;
        card.style.setProperty('--glare-x', `${glareX}%`);
        card.style.setProperty('--glare-y', `${glareY}%`);

        frameId = requestAnimationFrame(updateTilt);
      }

      card.addEventListener('mouseenter', () => {
        isHovered = true;
        if (!frameId) frameId = requestAnimationFrame(updateTilt);
      });

      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Normalized: -1 to 1
        targetX = ((x / rect.width) * 2 - 1);
        targetY = ((y / rect.height) * 2 - 1);

        // Glare percentage coordinates
        glareX = Math.round((x / rect.width) * 100);
        glareY = Math.round((y / rect.height) * 100);

        if (!frameId) frameId = requestAnimationFrame(updateTilt);
      });

      card.addEventListener('mouseleave', () => {
        isHovered = false;
        targetX = 0;
        targetY = 0;
      });
    });
  }

  /* ==========================================================================
     3. 3D ORBITAL CHIPS PARALLAX & HOVER DEPTH
     ========================================================================== */
  function initOrbitalChips() {
    const chips = document.querySelectorAll('.fhp-3d-orbital-chip');
    if (!chips.length || prefersReducedMotion) return;

    chips.forEach(chip => {
      chip.addEventListener('mouseenter', () => {
        chip.style.transform = 'translateZ(75px) scale(1.08)';
      });

      chip.addEventListener('mouseleave', () => {
        chip.style.transform = '';
      });
    });
  }

  // Initialize on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initHero3DCanvas();
      init3DTiltCards();
      initOrbitalChips();
    });
  } else {
    initHero3DCanvas();
    init3DTiltCards();
    initOrbitalChips();
  }
})();
