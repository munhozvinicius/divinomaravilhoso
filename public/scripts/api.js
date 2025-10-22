const API_BASE = '';

const FALLBACK_EVENTS = [
  {
    id: 1,
    title: 'BelzeBeer',
    date_iso: '2024-10-12',
    date_label: '12/10/2024',
    city: 'São Paulo · SP',
    venue: 'BelzeBeer',
    status: 'confirmado',
    description: 'Estreia da turnê com repertório dançante e jam session após o show.',
    tickets_link: null,
    instagram_url: 'https://www.instagram.com/belzebeer/'
  },
  {
    id: 2,
    title: 'La Cancha',
    date_iso: '2024-10-24',
    date_label: '24/10/2024',
    city: 'São Paulo · SP',
    venue: 'La Cancha',
    status: 'confirmado',
    description: 'Noite latina com grooves tropicais, convidado especial e pista até tarde.',
    tickets_link: null,
    instagram_url: 'https://www.instagram.com/lacanchafc/'
  },
  {
    id: 3,
    title: 'São Jorge Bar de Reza',
    date_iso: '2024-10-26',
    date_label: '26/10/2024',
    city: 'Santo André · SP',
    venue: 'São Jorge Bar de Reza',
    status: 'confirmado',
    description: 'Celebração de sábado com visual psicodélico e coro coletivo nos clássicos.',
    tickets_link: null,
    instagram_url: 'https://www.instagram.com/saojorgebardereza/'
  },
  {
    id: 4,
    title: 'Evento Privado',
    date_iso: '2024-11-21',
    date_label: '21/11/2024',
    city: 'Local reservado',
    venue: 'Evento Corporativo',
    status: 'evento privado',
    description: 'Apresentação exclusiva para convidados com repertório personalizado.',
    tickets_link: null,
    instagram_url: null
  }
];

const FALLBACK_TOP_TRACKS = [
  { track_name: 'A LUZ DE TIETA', votos: 18 },
  { track_name: 'SAMBA MAKOSSA', votos: 14 },
  { track_name: 'SUBIRUSDOISTIOZIN', votos: 12 },
  { track_name: 'BOGOTÁ', votos: 9 },
  { track_name: 'ENVOLVIDÃO', votos: 7 },
  { track_name: 'VARIAS QUEIXAS', votos: 6 },
  { track_name: 'ODARA', votos: 5 },
  { track_name: 'PIRANHA', votos: 5 },
  { track_name: 'CACHIMBO DA PAZ', votos: 4 },
  { track_name: 'O TELEFONE TOCOU NOVAMENTE', votos: 4 }
];

const FALLBACK_SETLIST_TRACKS = [
  'A LUZ DE TIETA',
  'ALMA SEBOSA / FLUTUA',
  'BOGOTÁ',
  'BOM SENSO',
  'CACHIMBO DA PAZ',
  'CAETANO VELOSO',
  'CIRANDA DE MALUCO',
  'CONTEXTO',
  'CRUA',
  'CUBA',
  'DEIXA EU DIZER / DESABAFO',
  'DESCOBRIDOR DOS 7 MARES',
  'DIG DIG DIG / DUAS CIDADES',
  'ELA PARTIU',
  'ENGENHO DE DENTRO',
  'FORA DA LEI',
  'FUNK ATÉ O CAROÇO',
  'GUINÉ BISSAU',
  'KILARIO',
  'LILÁS',
  'LUCRO',
  'MANGUETOWN',
  'MANUEL',
  'MAR DE GENTE',
  'ME DEIXA',
  'NÃO EXISTE AMOR EM SP',
  'NEM VEM QUE NÃO TEM',
  'O QUE SOBROU DO CÉU',
  'ODARA',
  'PARA LENNON E MCCARTNEY',
  'PIRANHA',
  'PRAIEIRA / SOSSEGO',
  'QUAL É',
  'QUANDO A MARÉ ENCHER',
  'RETRATO PRA IAIÁ',
  'SAMBA MAKOSSA',
  'SUBIRUSDOISTIOZIN',
  'SULAMERICANO',
  'VAI VENDO',
  'VOCÊ',
  'A FLOR',
  'AQUELE ABRAÇO',
  'ENVOLVIDÃO',
  'FALADOR PASSA MAL',
  'JORGE DA CAPADÓCIA',
  'JORGE MARAVILHA',
  'KRIOLA',
  'NA FRENTE DO RETO',
  'O TELEFONE TOCOU NOVAMENTE',
  'OBA, LÁ VEM ELA',
  'SALVE SIMPATIA',
  'SEGURA A NEGA',
  'VARIAS QUEIXAS'
].map((track_name, index) => ({
  track_name,
  slug: track_name
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, ''),
  position: index + 1
}));

const NOW_ISO = new Date('2024-10-01T19:30:00Z');

const FALLBACK_COMMENTS = [
  {
    contributor_name: 'Luana',
    idea: 'Mashup de Gal Costa com beats eletrônicos da cena Recife.',
    created_at: NOW_ISO.toISOString()
  },
  {
    contributor_name: 'DJ Cortez',
    idea: 'Quero uma versão funk de Odara com metais ao vivo!',
    created_at: new Date('2024-09-28T22:10:00Z').toISOString()
  },
  {
    contributor_name: null,
    idea: 'Misturar Jorge Ben com Mano Brown para um coro coletivo.',
    created_at: new Date('2024-09-25T18:45:00Z').toISOString()
  }
];

const API_FALLBACKS = {
  '/api/events': FALLBACK_EVENTS,
  '/api/setlist/top': FALLBACK_TOP_TRACKS,
  '/api/setlist/tracks': FALLBACK_SETLIST_TRACKS,
  '/api/setlist/comments': FALLBACK_COMMENTS
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function resolveFallback(path, explicitFallback) {
  if (explicitFallback) return clone(explicitFallback);
  const basePath = path.split('?')[0];
  const fallback = API_FALLBACKS[basePath];
  return fallback ? clone(fallback) : [];
}

export async function fetchJSON(path, fallback) {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) throw new Error('Resposta não OK');
    return await response.json();
  } catch (error) {
    console.warn(`Falha ao carregar ${path}:`, error.message);
    return resolveFallback(path, fallback);
  }
}

export async function postJSON(path, payload) {
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

export { API_BASE, API_FALLBACKS };
