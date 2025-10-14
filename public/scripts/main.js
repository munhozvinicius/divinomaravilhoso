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

function getDateParts(dateIso) {
  const date = new Date(`${dateIso}T00:00:00`);
  const day = date.toLocaleDateString('pt-BR', { day: '2-digit', timeZone: 'UTC' });
  const month = date.toLocaleDateString('pt-BR', { month: 'short', timeZone: 'UTC' }).replace('.', '').toUpperCase();
  const weekday = date
    .toLocaleDateString('pt-BR', { weekday: 'long', timeZone: 'UTC' })
    .replace(/^(\w)/, (match) => match.toUpperCase());
  const year = date.getFullYear();
  return { day, month, weekday, year };
}

function createAgendaCard(evento) {
  const article = document.createElement('article');
  article.className = 'agenda-card glass-panel';
  const { day, month, weekday, year } = getDateParts(evento.date_iso);

  const instagramButton =
    evento.instagram_url
      ? `
        <a class="btn btn-instagram" target="_blank" rel="noopener" href="${evento.instagram_url}">
          <span class="btn-icon" aria-hidden="true">📸</span>
          Instagram do local
        </a>
      `
      : '';

  const shareLabel = `${evento.title} ${day}-${month}-${year}`
    .replace(/[^a-zA-Z0-9-_]/g, '-')
    .replace(/-+/g, '-');
  const shareButton = `
    <a
      class="btn btn-outline btn-share"
      href="/api/events/${evento.id}/story-card.png"
      target="_blank"
      download="divino-${shareLabel}.png"
    >
      Salvar lambe-lambe
    </a>
  `;

  const ticketsButton =
    evento.tickets_link
      ? `
        <a class="btn btn-outline" target="_blank" rel="noopener" href="${evento.tickets_link}">Ingressos</a>
      `
      : '';

  const actions = [instagramButton, ticketsButton, shareButton].filter(Boolean).join('');

  article.innerHTML = `
    <header class="agenda-card-header">
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
    </header>
    ${evento.description ? `<p class="agenda-description">${evento.description}</p>` : ''}
    <div class="agenda-actions">${actions}</div>
  `;
  return article;
}

async function renderAgenda() {
  const container = document.getElementById('agenda-cards');
  if (!container) return;
  container.innerHTML = '';
  const eventos = await fetchJSON('/api/events');
  if (!Array.isArray(eventos) || eventos.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Em breve novas datas neon.';
    container.appendChild(empty);
    return;
  }
  eventos.slice(0, 4).forEach((evento) => {
    container.appendChild(createAgendaCard(evento));
  });
}

async function renderTopTracks() {
  const list = document.getElementById('top-tracks');
  if (!list) return;
  list.innerHTML = '';
  const tracks = await fetchJSON('/api/setlist/top');
  if (!Array.isArray(tracks) || tracks.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Seja a primeira pessoa a votar na setlist!';
    list.appendChild(empty);
    return;
  }
  tracks.forEach((track, index) => {
    const item = document.createElement('li');
    item.innerHTML = `
      <span class="track-rank">#${index + 1}</span>
      <span class="track-name">${track.track_name}</span>
      <span class="track-votes">${track.votos} voto${track.votos === 1 ? '' : 's'}</span>
    `;
    list.appendChild(item);
  });
}

function formatRelative(dateIso) {
  try {
    const date = new Date(dateIso);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '';
  }
}

async function renderComments() {
  const container = document.getElementById('setlist-comments');
  if (!container) return;
  container.innerHTML = '';
  const comments = await fetchJSON('/api/setlist/comments?limit=12');
  if (!Array.isArray(comments) || comments.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Deixe sua ideia para inaugurar o mural neon!';
    container.appendChild(empty);
    return;
  }
  comments.forEach((comment) => {
    const item = document.createElement('article');
    item.className = 'comment-item';
    item.innerHTML = `
      <header>
        <strong>${comment.contributor_name || 'Anônimo neon'}</strong>
        <time>${formatRelative(comment.created_at)}</time>
      </header>
      <p>${comment.idea}</p>
    `;
    container.appendChild(item);
  });
}

async function postJSON(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Falha ao enviar');
  }
  return response.json();
}

function handleSetlistVote() {
  const form = document.getElementById('setlist-form');
  const feedback = document.getElementById('vote-feedback');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    feedback.textContent = '';
    const data = Object.fromEntries(new FormData(form));
    try {
      await postJSON('/api/setlist/vote', data);
      form.reset();
      feedback.textContent = 'Voto registrado! Obrigado por iluminar o set.';
      feedback.classList.remove('error');
      await renderTopTracks();
    } catch (error) {
      feedback.textContent = 'Não foi possível registrar o voto. Tente novamente.';
      feedback.classList.add('error');
    }
  });
}

function handleCommentForm() {
  const form = document.getElementById('comment-form');
  const feedback = document.getElementById('comment-feedback');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    feedback.textContent = '';
    const data = Object.fromEntries(new FormData(form));
    try {
      await postJSON('/api/setlist/comment', data);
      form.reset();
      feedback.textContent = 'Sugestão recebida! Vamos analisar com carinho.';
      feedback.classList.remove('error');
      await renderComments();
    } catch (error) {
      feedback.textContent = 'Não rolou enviar agora. Pode tentar de novo?';
      feedback.classList.add('error');
    }
  });
}

function handleNewsletter() {
  const form = document.getElementById('newsletter-form');
  const feedback = document.getElementById('newsletter-feedback');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    feedback.textContent = '';
    const data = Object.fromEntries(new FormData(form));
    try {
      await postJSON('/api/newsletter', data);
      form.reset();
      feedback.textContent = 'Você está na lista! Enviaremos o drop neon em primeira mão.';
      feedback.classList.remove('error');
    } catch (error) {
      feedback.textContent = 'Não conseguimos salvar seu e-mail agora. Tente novamente.';
      feedback.classList.add('error');
    }
  });
}

renderAgenda();
renderTopTracks();
renderComments();
handleSetlistVote();
handleCommentForm();
handleNewsletter();
