// Orchestrate intro animation and then reveal the nav (acordeón)
(function () {
  const intro = document.getElementById('intro');
  const nav = document.querySelector('nav');
  const header = document.querySelector('.site-header');

  if (!intro || !nav) return;

  // Duration values (ms)
  const introTotal = 1800;
  const hold = 700; // time to hold logo at top before revealing nav

  function finishIntro() {
    intro.classList.add('intro-done');
    // reveal header and then show nav after overlay fades
    if (header) {
      header.classList.add('visible');
      header.setAttribute('aria-hidden', 'false');
    }
    setTimeout(() => nav.classList.add('visible'), 300);
    // hide intro from accessibility tree
    intro.setAttribute('aria-hidden', 'true');
  }

  // allow skipping intro by click or any key
  function skip() {
    finishIntro();
    window.removeEventListener('keydown', skip);
    intro.removeEventListener('click', skip);
  }

  window.addEventListener('keydown', skip, { once: true });
  intro.addEventListener('click', skip, { once: true });

  // main timer: pop -> move up -> finish
  setTimeout(() => {
    // after initial pop animation
    // move logo to top by adding a class: we reuse intro-done transformations visually
    intro.querySelector('.intro-logo').style.transform = 'scale(.6) translateY(-38vh)';
  }, 1000);

  setTimeout(() => {
    finishIntro();
  }, introTotal + hold);

  // --- Title toggle logic for each item ---
  function hideAllTitles() {
    document.querySelectorAll('.item-title.visible').forEach(t => {
      t.classList.remove('visible');
      t.setAttribute('aria-hidden', 'true');
    });
  }

  // delegate clicks on nav anchors
  nav.addEventListener('click', function (ev) {
    const a = ev.target.closest('a');
    if (!a || !nav.contains(a)) return;

    const title = a.querySelector('.item-title');

    // decide target URL: prefer data-url, else href
    const targetUrl = a.dataset.url || a.getAttribute('href');

    const isZoomed = a.classList.contains('zoomed');

    if (!isZoomed) {
      // first click: prevent navigation, show zoom/visual state and the title
      ev.preventDefault();
      hideAllTitles();
      // remove zoom from any other item
      nav.querySelectorAll('a.zoomed').forEach(x => x.classList.remove('zoomed'));
      a.classList.add('zoomed');
      if (title) {
        title.classList.add('visible');
        title.setAttribute('aria-hidden', 'false');
      }
      // move focus for keyboard users
      a.focus();
    } else {
      // second click: if there's a meaningful URL, navigate there; otherwise toggle off
      if (targetUrl && targetUrl !== '#' && targetUrl !== '') {
        // allow navigation by setting location (works even if href is '#')
        window.location.href = targetUrl;
      } else {
        // no destination: remove zoom and hide title
        a.classList.remove('zoomed');
        if (title) {
          title.classList.remove('visible');
          title.setAttribute('aria-hidden', 'true');
        }
        // prevent default if href is '#'
        ev.preventDefault();
      }
    }
  });

  // click outside navigation clears zoomed state
  document.addEventListener('click', function (ev) {
    if (!ev.target.closest('nav')) {
      nav.querySelectorAll('a.zoomed').forEach(a => {
        a.classList.remove('zoomed');
        const t = a.querySelector('.item-title');
        if (t) { t.classList.remove('visible'); t.setAttribute('aria-hidden', 'true'); }
      });
    }
  });

  // ESC clears zoomed state
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      nav.querySelectorAll('a.zoomed').forEach(a => {
        a.classList.remove('zoomed');
        const t = a.querySelector('.item-title');
        if (t) { t.classList.remove('visible'); t.setAttribute('aria-hidden', 'true'); }
      });
    }
  });

  // keyboard support: Enter/Space toggles focused anchor
  nav.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter' || ev.key === ' ') {
      const a = document.activeElement;
      if (a && a.tagName === 'A' && nav.contains(a)) {
        ev.preventDefault();
        a.click();
      }
    }
  });

  // pointer hover support: show title when pointer enters an item, hide when leaves
  nav.querySelectorAll('a').forEach(a => {
    a.addEventListener('pointerenter', function () {
      const title = a.querySelector('.item-title');
      if (!title) return;
      hideAllTitles();
      title.classList.add('visible');
      title.setAttribute('aria-hidden', 'false');
    });
    a.addEventListener('pointerleave', function () {
      const title = a.querySelector('.item-title');
      if (!title) return;
      title.classList.remove('visible');
      title.setAttribute('aria-hidden', 'true');
    });
  });
})();

