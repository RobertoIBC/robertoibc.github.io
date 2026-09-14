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
