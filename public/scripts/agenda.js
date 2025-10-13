async function fetchAgenda() {
  try {
    const response = await fetch('/api/events');
    if (!response.ok) throw new Error('Falha ao carregar agenda');
    return await response.json();
  } catch (error) {
    console.error(error);
    return [];
  }
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

function createScheduleItem(evento) {
  const article = document.createElement('article');
  article.className = 'schedule-item';
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
    ${actions ? `<div class="schedule-actions">${actions}</div>` : ''}
  `;
  return article;
}

async function renderSchedule() {
  const container = document.getElementById('schedule-list');
  if (!container) return;
  const eventos = await fetchAgenda();
  if (eventos.length === 0) {
    container.innerHTML = '<p>Em breve novas datas.</p>';
    return;
  }
  eventos.forEach((evento) => container.appendChild(createScheduleItem(evento)));
}

renderSchedule();
