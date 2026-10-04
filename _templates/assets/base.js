  // Cabecera: fondo solido al hacer scroll
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => nav.classList.toggle('scrolled', scrollY > 80));

  // Menu movil
  const menuToggle = document.getElementById('menuToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const menuBackdrop = document.getElementById('menuBackdrop');
  function closeMenu() {
    menuToggle.classList.remove('open'); mobileMenu.classList.remove('open'); menuBackdrop.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false'); document.body.style.overflow = '';
  }
  function openMenu() {
    menuToggle.classList.add('open'); mobileMenu.classList.add('open'); menuBackdrop.classList.add('open');
    menuToggle.setAttribute('aria-expanded', 'true'); document.body.style.overflow = 'hidden';
  }
  menuToggle.addEventListener('click', () => mobileMenu.classList.contains('open') ? closeMenu() : openMenu());
  menuBackdrop.addEventListener('click', closeMenu);
  mobileMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));

  // Animaciones de entrada (.rv, .rvl, .rvr)
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('on'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll('.rv, .rvl, .rvr').forEach(el => io.observe(el));

  // Burbuja de WhatsApp: a los 6 s; si se cierra (o se pulsa) no vuelve en la sesion.
  // sessionStorage puede fallar (modo privado, cookies bloqueadas): la pagina funciona igual.
  (function () {
    const b = document.getElementById('waBurbuja');
    if (!b) return;
    const K = 'oya-wa-burbuja';
    try { if (sessionStorage.getItem(K)) return; } catch (e) {}
    const recordar = () => { try { sessionStorage.setItem(K, '1'); } catch (e) {} };
    const cerrar = () => { b.classList.remove('visible'); b.hidden = true; recordar(); };
    setTimeout(() => {
      b.hidden = false;
      requestAnimationFrame(() => requestAnimationFrame(() => b.classList.add('visible')));
    }, 6000);
    b.querySelector('.wa-burbuja-cerrar').addEventListener('click', cerrar);
    b.querySelector('.wa-burbuja-texto').addEventListener('click', () => { recordar(); setTimeout(cerrar, 300); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !b.hidden) cerrar(); });
  })();
