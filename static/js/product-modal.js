document.addEventListener('DOMContentLoaded', () => {
  const modalHtml = `
    <div class="modal-overlay" tabindex="-1">
      <div class="modal-box" role="dialog" aria-modal="true">
        <button type="button" class="modal-close" aria-label="Cerrar ventana">&times;</button>
        <div class="modal-image-wrap">
          <button type="button" class="modal-nav modal-nav--prev" aria-label="Imagen anterior">‹</button>
          <img class="modal-image" src="" alt="">
          <div class="modal-image-counter" aria-live="polite"></div>
          <button type="button" class="modal-nav modal-nav--next" aria-label="Siguiente imagen">›</button>
          <div class="modal-gallery"></div>
        </div>
        <div class="modal-body">
          <h2 class="modal-title"></h2>
          <p class="modal-price"></p>
          <p class="modal-description"></p>
          <p class="modal-quantity"></p>
          <a class="card-joya__button modal-add-button" href="#">Agregar al carrito</a>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const overlay = document.querySelector('.modal-overlay');
  const modalCloseButton = overlay.querySelector('.modal-close');
  const modalImage = overlay.querySelector('.modal-image');
  const modalGallery = overlay.querySelector('.modal-gallery');
  const modalPrevButton = overlay.querySelector('.modal-nav--prev');
  const modalNextButton = overlay.querySelector('.modal-nav--next');
  const modalTitle = overlay.querySelector('.modal-title');
  const modalPrice = overlay.querySelector('.modal-price');
  const modalDescription = overlay.querySelector('.modal-description');
  const modalQuantity = overlay.querySelector('.modal-quantity');
  const modalImageCounter = overlay.querySelector('.modal-image-counter');
  const modalAddButton = overlay.querySelector('.modal-add-button');

  let currentGalleryUrls = [];
  let currentImageIndex = 0;

  function updateModalImage(index) {
    if (!currentGalleryUrls.length) return;
    currentImageIndex = Math.max(0, Math.min(index, currentGalleryUrls.length - 1));
    modalImage.src = currentGalleryUrls[currentImageIndex];
    modalPrevButton.disabled = currentImageIndex === 0;
    modalNextButton.disabled = currentImageIndex === currentGalleryUrls.length - 1;
    const showCounter = currentGalleryUrls.length > 1;
    modalImageCounter.textContent = showCounter
      ? `Foto ${currentImageIndex + 1} de ${currentGalleryUrls.length}`
      : '';
    modalImageCounter.style.display = showCounter ? 'block' : 'none';
  }

  function renderGallery(urls) {
    currentGalleryUrls = Array.isArray(urls) ? urls.filter((url) => url && url.trim()) : [];
    currentImageIndex = 0;
    modalGallery.style.display = 'none';

    if (!currentGalleryUrls.length) {
      modalPrevButton.style.display = 'none';
      modalNextButton.style.display = 'none';
      modalImageCounter.style.display = 'none';
      modalImage.src = '';
      return;
    }

    const showControls = currentGalleryUrls.length > 1;
    modalPrevButton.style.display = showControls ? 'block' : 'none';
    modalNextButton.style.display = showControls ? 'block' : 'none';
    updateModalImage(0);
  }

  function openModal(product) {
    if (!product) return;
    let galleryUrls = Array.isArray(product.gallery)
      ? product.gallery
      : Array.isArray(product.gallery_urls)
      ? product.gallery_urls
      : [];
    galleryUrls = galleryUrls.filter((url) => typeof url === 'string' && url.trim());

    modalImage.alt = product.nombre || 'Producto';
    modalTitle.textContent = product.nombre || 'Producto';
    modalPrice.textContent = product.precio ? `$${product.precio}` : 'Precio no disponible';
    modalDescription.textContent = product.descripcion || 'Descripción no disponible.';
    modalQuantity.textContent = product.cantidad ? `Cantidad: ${product.cantidad}` : 'Cantidad: N/A';
    modalAddButton.href = `/carrito/agregar/${product.tipo || 'producto'}/${product.id}/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    renderGallery(galleryUrls.length ? galleryUrls : [product.imagen || '']);
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  overlay.addEventListener('click', (event) => {
    if (event.target === overlay || event.target === modalCloseButton) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && overlay.classList.contains('open')) {
      closeModal();
    }
    if (overlay.classList.contains('open')) {
      if (event.key === 'ArrowRight') {
        updateModalImage(currentImageIndex + 1);
      }
      if (event.key === 'ArrowLeft') {
        updateModalImage(currentImageIndex - 1);
      }
    }
  });

  modalPrevButton.addEventListener('click', () => updateModalImage(currentImageIndex - 1));
  modalNextButton.addEventListener('click', () => updateModalImage(currentImageIndex + 1));

  function parseGalleryData(value) {
    if (!value) return [];
    const trimmed = value.trim();
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      try {
        const parsed = JSON.parse(trimmed);
        return Array.isArray(parsed) ? parsed.map((url) => String(url).trim()).filter(Boolean) : [];
      } catch (error) {
        return [];
      }
    }
    return trimmed.split('|;|').map((url) => url.trim()).filter(Boolean);
  }

  function getProductData(card) {
    if (!card) return null;
    const image = card.querySelector('img');
    const name = card.dataset.productName || card.querySelector('.product-card__name, .search-result-card h2')?.textContent.trim() || '';
    const price = card.dataset.productPrice || card.querySelector('.product-card__price, .search-result-card p')?.textContent.replace(/[^0-9.,]/g, '').trim() || '';
    const description = card.dataset.productDescription || '';
    const quantity = card.dataset.productQuantity || '';
    const gallery = parseGalleryData(card.dataset.gallery || '');
    return {
      id: card.dataset.productId || '',
      nombre: name,
      precio: price,
      descripcion: description,
      cantidad: quantity,
      imagen: image?.src || '',
      tipo: card.dataset.productType || 'producto',
      gallery,
    };
  }

  document.body.addEventListener('click', (event) => {
    if (event.target.closest('.card-joya__button') || event.target.closest('.modal-close')) return;
    const card = event.target.closest('.product-card, .search-result-card');
    if (!card) return;
    event.preventDefault();
    const product = getProductData(card);
    openModal(product);
  });
});