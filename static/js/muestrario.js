const grid = document.getElementById('joyeria-grid');
const dataElement = document.getElementById('joyeria-data');

if (grid && dataElement) {
  let productos = [];
  try {
    productos = JSON.parse(dataElement.textContent.trim() || '[]');
  } catch (error) {
    console.error('Error parseando los datos del muestrario:', error);
    productos = [];
  }

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-box">
      <button type="button" class="modal-close" aria-label="Cerrar ventana">&times;</button>
      <div class="modal-image-wrap">
        <button type="button" class="modal-nav modal-nav--prev" aria-label="Imagen anterior">‹</button>
        <img class="modal-image" src="" alt="">
        <div class="modal-image-counter" aria-live="polite"></div>
        <button type="button" class="modal-nav modal-nav--next" aria-label="Siguiente imagen">›</button>
      </div>
      <div class="modal-body">
        <h2 class="modal-title"></h2>
        <p class="modal-price"></p>
        <p class="modal-description"></p>
        <p class="modal-quantity"></p>
        <a class="card-joya__button modal-add-button" href="#">Agregar al carrito</a>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const modalCloseButton = overlay.querySelector('.modal-close');
  const modalImage = overlay.querySelector('.modal-image');
  const modalPrevButton = overlay.querySelector('.modal-nav--prev');
  const modalNextButton = overlay.querySelector('.modal-nav--next');
  const modalImageCounter = overlay.querySelector('.modal-image-counter');
  const modalTitle = overlay.querySelector('.modal-title');
  const modalPrice = overlay.querySelector('.modal-price');
  const modalDescription = overlay.querySelector('.modal-description');
  const modalQuantity = overlay.querySelector('.modal-quantity');
  const modalAddButton = overlay.querySelector('.modal-add-button');

  let currentGalleryUrls = [];
  let currentImageIndex = 0;

  function updateProductModalImage(index) {
    if (!currentGalleryUrls.length) return;
    currentImageIndex = Math.max(0, Math.min(index, currentGalleryUrls.length - 1));
    modalImage.src = currentGalleryUrls[currentImageIndex] || '';
    modalPrevButton.disabled = currentImageIndex === 0;
    modalNextButton.disabled = currentImageIndex === currentGalleryUrls.length - 1;
    modalImageCounter.textContent = currentGalleryUrls.length > 1
      ? `Foto ${currentImageIndex + 1} de ${currentGalleryUrls.length}`
      : '';
  }

  function openProductModal(product) {
    if (!product) return;
    modalTitle.textContent = product.nombre;
    modalPrice.textContent = `$${product.precio}`;
    modalDescription.textContent = product.descripcion || 'Descripción no disponible.';
    modalQuantity.textContent = `Cantidad: ${product.cantidad != null ? product.cantidad : 'N/A'}`;
    currentGalleryUrls = Array.isArray(product.gallery_urls) && product.gallery_urls.length
      ? product.gallery_urls
      : product.imagen
      ? [product.imagen]
      : [];

    updateProductModalImage(0);
    modalPrevButton.style.display = currentGalleryUrls.length > 1 ? 'block' : 'none';
    modalNextButton.style.display = currentGalleryUrls.length > 1 ? 'block' : 'none';
    modalImageCounter.style.display = currentGalleryUrls.length > 1 ? 'block' : 'none';
    modalAddButton.href = `/carrito/agregar/${product.tipo}/${product.id}/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
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

  modalPrevButton.addEventListener('click', () => updateProductModalImage(currentImageIndex - 1));
  modalNextButton.addEventListener('click', () => updateProductModalImage(currentImageIndex + 1));

  document.addEventListener('keydown', (event) => {
    if (!overlay.classList.contains('open')) return;
    if (event.key === 'Escape') {
      closeModal();
    }
    if (event.key === 'ArrowRight') {
      updateProductModalImage(currentImageIndex + 1);
    }
    if (event.key === 'ArrowLeft') {
      updateProductModalImage(currentImageIndex - 1);
    }
  });

  grid.addEventListener('click', (event) => {
    if (event.target.closest('.card-joya__button')) return;
    const card = event.target.closest('.card-joya');
    if (!card) return;
    const index = card.dataset.productIndex;
    if (index == null) return;
    openProductModal(productos[Number(index)]);
  });

  let productQueue = [];

  function shuffleProductIndices() {
    productQueue = productos.map((_, index) => index);
    for (let i = productQueue.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [productQueue[i], productQueue[j]] = [productQueue[j], productQueue[i]];
    }
  }

  function getNextProductIndices(count) {
    if (productQueue.length < count) {
      const remaining = productQueue.splice(0);
      shuffleProductIndices();
      while (remaining.length < count && productQueue.length) {
        remaining.push(productQueue.shift());
      }
      return remaining;
    }
    return productQueue.splice(0, count);
  }

  function renderizarMuestrario() {
    if (!productos.length) {
      grid.classList.remove('is-fading');
      grid.innerHTML = '<div class="joyeria-empty">No hay productos para mostrar.</div>';
      return;
    }

    if (!productQueue.length) {
      shuffleProductIndices();
    }

    grid.classList.add('is-fading');
    grid.style.pointerEvents = 'none';

    setTimeout(() => {
      grid.innerHTML = '';
      const itemsAMostrar = Math.min(6, productos.length);
      const indices = getNextProductIndices(itemsAMostrar);

      indices.forEach((idx) => {
        const p = productos[idx];
        const tipo = p.tipo || 'joya';
        const imagenHtml = p.imagen
          ? `<img src="${p.imagen}" alt="${p.nombre}">`
          : '<div class="gallery-item__placeholder">Sin imagen</div>';
        const editButtonHtml = p.admin_url ? `<a href="${p.admin_url}" class="card-joya__button admin-edit-button" target="_blank" rel="noopener noreferrer">Editar producto</a>` : '';

        grid.innerHTML += `
          <div class="card-joya ${tipo === 'joya' ? 'card-joya--joya' : 'card-joya--producto'}" data-product-index="${idx}">
            ${imagenHtml}
            <h3>${p.nombre}</h3>
            <p class="card-joya__price">$${p.precio}</p>
            ${p.descripcion ? `<p class="card-joya__desc">${p.descripcion}</p>` : ''}
            <div class="product-card__actions">
              <a href="/carrito/agregar/${tipo}/${p.id}/?next=${encodeURIComponent(window.location.pathname + window.location.search)}" class="card-joya__button">
                Agregar al carrito
              </a>
              ${editButtonHtml}
            </div>
          </div>
        `;
      });

      grid.classList.remove('is-fading');
      grid.style.pointerEvents = '';
    }, 180);
  }

  renderizarMuestrario();
  setInterval(renderizarMuestrario, 4200);
}
