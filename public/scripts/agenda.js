import { fetchJSON } from './api.js';

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

function createScheduleItem(evento) {
  const article = document.createElement('article');
  article.className = 'schedule-item glass-panel';
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
    <div class="schedule-head">
      <div class="schedule-date">
        <span class="schedule-day">${day}</span>
        <span class="schedule-month">${month}</span>
      </div>
      <div class="schedule-info">
        ${evento.status ? `<span class="tag">${evento.status}</span>` : ''}
        <strong>${evento.title}</strong>
        <span class="schedule-meta">${weekday} · ${evento.date_label}</span>
        <span class="schedule-venue">${evento.venue}</span>
        <span class="schedule-city">${evento.city}</span>
      </div>
    </div>
    ${evento.description ? `<p class="schedule-description">${evento.description}</p>` : ''}
    <div class="schedule-actions">${actions}</div>
  `;
  return article;
}

async function renderSchedule() {
  const container = document.getElementById('schedule-list');
  if (!container) return;
  const eventos = await fetchJSON('/api/events');
  container.innerHTML = '';
  if (eventos.length === 0) {
    container.innerHTML = '<p class="empty-state">Em breve novas datas neon.</p>';
    return;
  }
  eventos.forEach((evento) => container.appendChild(createScheduleItem(evento)));
}

renderSchedule();
