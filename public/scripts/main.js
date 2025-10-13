const API_BASE = '';

async function fetchJSON(path, fallback = []) {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) throw new Error('Resposta não OK');
    return await response.json();
  } catch (error) {
    console.warn(`Falha ao carregar ${path}:`, error.message);
    return fallback;
  }
}

function formatCurrency(value) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

function getDateParts(dateIso) {
  const date = new Date(`${dateIso}T00:00:00`);
  const day = date.toLocaleDateString('pt-BR', { day: '2-digit', timeZone: 'UTC' });
  const monthRaw = date.toLocaleDateString('pt-BR', { month: 'short', timeZone: 'UTC' });
  const weekdayRaw = date.toLocaleDateString('pt-BR', { weekday: 'long', timeZone: 'UTC' });
  const month = monthRaw.replace('.', '').toUpperCase();
  const weekday = weekdayRaw.charAt(0).toUpperCase() + weekdayRaw.slice(1);
  return { day, month, weekday };
}

function createAgendaCard(evento) {
  const article = document.createElement('article');
  article.className = 'agenda-card';
  const { day, month, weekday } = getDateParts(evento.date_iso);
  const instagramButton =
    evento.instagram_url
      ? `
        <a class="btn btn-instagram" target="_blank" rel="noopener" href="${evento.instagram_url}">
          <span class="btn-icon" aria-hidden="true">📸</span>
          <span>Instagram do local</span>
        </a>
      `
      : '';
  const ticketsButton =
    evento.tickets_link
      ? `
        <a class="btn btn-outline btn-outline-dark" target="_blank" rel="noopener" href="${evento.tickets_link}">
          Ingressos
        </a>
      `
      : '';
  const actions = [instagramButton, ticketsButton].filter(Boolean).join('');
  article.innerHTML = `
    <div class="agenda-card-header">
      <div class="agenda-date">
        <span class="agenda-day">${day}</span>
        <span class="agenda-month">${month}</span>
      </div>
      <div class="agenda-info">
        <span class="tag">${evento.status || 'confirmado'}</span>
        <h3>${evento.title}</h3>
        <p class="agenda-meta">${weekday} · ${evento.date_label}</p>
        <p class="agenda-venue">${evento.venue}</p>
        <p class="agenda-city">${evento.city}</p>
      </div>
    </div>
    ${evento.description ? `<p class="agenda-description">${evento.description}</p>` : ''}
    ${actions ? `<div class="agenda-actions">${actions}</div>` : ''}
  `;
  return article;
}

function createProductCard(produto) {
  const card = document.createElement('article');
  card.className = 'product-card';
  card.innerHTML = `
    <div class="product-illustration">${produto.category}</div>
    <span class="badge">${produto.is_new ? 'lançamento' : 'clássico'}</span>
    <h3>${produto.name}</h3>
    <p>${produto.description}</p>
    <span class="price">${formatCurrency(produto.price)}</span>
    <button class="btn btn-primary" data-product-id="${produto.id}">Adicionar</button>
  `;
  return card;
}

const cart = {
  items: new Map(),
  load() {
    const saved = localStorage.getItem('divino-cart');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        parsed.forEach((item) => this.items.set(item.id, item));
      } catch (error) {
        console.warn('Falha ao restaurar carrinho:', error.message);
      }
    }
  },
  persist() {
    localStorage.setItem('divino-cart', JSON.stringify(Array.from(this.items.values())));
  },
  add(product) {
    const existing = this.items.get(product.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      this.items.set(product.id, { ...product, quantity: 1 });
    }
    this.persist();
  },
  remove(productId) {
    this.items.delete(productId);
    this.persist();
  },
  clear() {
    this.items.clear();
    this.persist();
  },
  summary() {
    const total = Array.from(this.items.values()).reduce(
      (acc, item) => acc + item.price * item.quantity,
      0
    );
    const quantity = Array.from(this.items.values()).reduce(
      (acc, item) => acc + item.quantity,
      0
    );
    return { total, quantity };
  }
};

function renderCart() {
  const container = document.getElementById('cart-items');
  if (!container) return;

  container.innerHTML = '';
  if (cart.items.size === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-cart';
    empty.textContent = 'O carrinho está vazio. Escolha seus itens favoritos.';
    container.appendChild(empty);
  } else {
    for (const item of cart.items.values()) {
      const row = document.createElement('div');
      row.className = 'cart-item';
      row.innerHTML = `
        <span>${item.name} × ${item.quantity}</span>
        <div>
          <strong>${formatCurrency(item.price * item.quantity)}</strong>
          <button class="remove-item" data-remove="${item.id}">remover</button>
        </div>
      `;
      container.appendChild(row);
    }
  }

  const { total, quantity } = cart.summary();
  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total');
  if (countEl) countEl.textContent = `${quantity} ${quantity === 1 ? 'item' : 'itens'}`;
  if (totalEl) totalEl.textContent = formatCurrency(total);
}

function attachCartListeners(products) {
  const storeGrid = document.getElementById('store-grid');
  if (storeGrid) {
    storeGrid.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-product-id]');
      if (!button) return;
      const productId = Number(button.dataset.productId);
      const product = products.find((p) => p.id === productId);
      if (product) {
        cart.add(product);
        renderCart();
      }
    });
  }

  const cartItems = document.getElementById('cart-items');
  if (cartItems) {
    cartItems.addEventListener('click', (event) => {
      const remove = event.target.closest('button[data-remove]');
      if (!remove) return;
      const productId = Number(remove.dataset.remove);
      cart.remove(productId);
      renderCart();
    });
  }
}

async function renderAgenda() {
  const eventos = await fetchJSON('/api/events');
  const container = document.getElementById('agenda-cards');
  if (!container) return;
  container.innerHTML = '';

  eventos.slice(0, 4).forEach((evento) => {
    container.appendChild(createAgendaCard(evento));
  });
}

async function renderProducts() {
  const produtos = await fetchJSON('/api/products');
  const grid = document.getElementById('store-grid');
  if (!grid) return;
  grid.innerHTML = '';

  produtos.forEach((produto) => {
    grid.appendChild(createProductCard(produto));
  });
  attachCartListeners(produtos);
}

async function renderSocialLinks() {
  const links = await fetchJSON('/api/social');
  const container = document.getElementById('social-links');
  if (!container) return;

  container.innerHTML = '';
  links.forEach((link) => {
    const anchor = document.createElement('a');
    anchor.href = link.url;
    anchor.target = '_blank';
    anchor.rel = 'noopener';
    anchor.textContent = link.label;
    container.appendChild(anchor);
  });
}

async function handleCheckout(event) {
  event.preventDefault();
  const feedback = document.getElementById('checkout-feedback');
  if (cart.items.size === 0) {
    feedback.textContent = 'Adicione itens ao carrinho antes de enviar o pedido.';
    feedback.style.color = '#b23427';
    return;
  }

  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    customer: {
      name: formData.get('nome'),
      email: formData.get('email'),
      phone: formData.get('telefone'),
      address: formData.get('endereco'),
      payment_method: formData.get('pagamento')
    },
    items: Array.from(cart.items.values()).map((item) => ({
      id: item.id,
      quantity: item.quantity
    }))
  };

  try {
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error('Falha ao registrar pedido');
    const data = await response.json();
    feedback.textContent = `Pedido recebido! Código: ${data.order_id}`;
    feedback.style.color = '#1b6f4e';
    form.reset();
    cart.clear();
    renderCart();
  } catch (error) {
    feedback.textContent = 'Não foi possível registrar o pedido agora. Tente novamente mais tarde.';
    feedback.style.color = '#b23427';
    console.error(error);
  }
}

async function handleNewsletter(event) {
  event.preventDefault();
  const input = document.getElementById('newsletter-email');
  const feedback = document.getElementById('newsletter-feedback');
  try {
    const response = await fetch('/api/newsletter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: input.value })
    });
    if (!response.ok) throw new Error('Falha no cadastro');
    feedback.textContent = 'E-mail cadastrado. Obrigado por fazer parte!';
    feedback.style.color = '#1b6f4e';
    input.value = '';
  } catch (error) {
    feedback.textContent = 'Não foi possível cadastrar agora.';
    feedback.style.color = '#b23427';
  }
}

function initForms() {
  const checkoutForm = document.getElementById('checkout-form');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', handleCheckout);
  }

  const newsletterForm = document.getElementById('newsletter-form');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', handleNewsletter);
  }
}

async function bootstrap() {
  cart.load();
  renderCart();
  await Promise.all([renderAgenda(), renderProducts(), renderSocialLinks()]);
  initForms();
}

bootstrap();
