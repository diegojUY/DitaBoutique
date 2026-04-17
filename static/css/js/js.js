// main.js — JS compartido en toda la aplicación

// Menú móvil
function toggleMobileMenu() {
  const nav = document.querySelector('.main-nav');
  if (!nav) return;
  const open = nav.style.display === 'flex';
  nav.style.display = open ? 'none' : 'flex';
  if (!open) {
    Object.assign(nav.style, {
      flexDirection: 'column',
      position: 'absolute',
      top: 'var(--header-height)',
      left: '0', right: '0',
      background: 'var(--color-black)',
      padding: '16px 0',
      zIndex: '99',
    });
  }
}

// Cerrar menú móvil al hacer clic afuera
document.addEventListener('click', function(e) {
  const header = document.querySelector('.site-header');
  const nav    = document.querySelector('.main-nav');
  const isMobileMenuOpen = nav && nav.style.display === 'flex' && nav.style.position === 'absolute';
  if (isMobileMenuOpen && header && nav && !header.contains(e.target)) {
    nav.style.display = 'none';
  }
});

// CSRF token helper para fetch()
function getCsrfToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')?.[1] ?? '';
}
window.getCsrfToken = getCsrfToken;

function initHomeGalleryRotation() {
  const slides = Array.from(document.querySelectorAll('.gallery-slide'));
  if (slides.length < 2) return;

  let activeIndex = 0;
  setInterval(() => {
    slides[activeIndex].classList.remove('is-active');
    activeIndex = (activeIndex + 1) % slides.length;
    slides[activeIndex].classList.add('is-active');
  }, 5000);
}

document.addEventListener('DOMContentLoaded', initHomeGalleryRotation);

// Wishlist toggle (llamado desde product_card.html)
async function toggleWishlist(event, btn) {
  event.preventDefault();
  const productId = btn.dataset.productId;
  try {
    const resp = await fetch(`/wishlist/toggle/${productId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/json',
      }
    });
    if (resp.ok) {
      const active = btn.classList.toggle('is-active');
      btn.textContent = active ? '\u2665' : '\u2661';
    }
  } catch(e) {
    console.error('Wishlist error:', e);
  }
}