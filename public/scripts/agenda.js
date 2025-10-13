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

function createScheduleItem(evento) {
  const article = document.createElement('article');
  article.className = 'schedule-item';
  article.innerHTML = `
    <strong>${evento.title}</strong>
    <span>${evento.date_label} · ${evento.city}</span>
    <span>${evento.venue}</span>
    ${evento.description ? `<p>${evento.description}</p>` : ''}
    ${evento.status ? `<span class="tag">${evento.status}</span>` : ''}
    ${evento.tickets_link ? `<a class="btn btn-outline" target="_blank" href="${evento.tickets_link}">Ingressos</a>` : ''}
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
