(function () {
  const trackNames = [
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
  ];

  const eventsFallback = [
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

  const fallbackUsage = new Set();

  function normalisePath(path) {
    if (!path) return '/';
    return path.startsWith('/') ? path : `/${path}`;
  }

  function resolveStoredApiBase() {
    const params = new URLSearchParams(window.location.search);
    const queryBase = params.get('apiBase');
    if (queryBase) {
      try {
        localStorage.setItem('divino:apiBase', queryBase);
      } catch (error) {
        console.warn('Não foi possível salvar apiBase no storage:', error);
      }
      return queryBase;
    }

    try {
      const stored = localStorage.getItem('divino:apiBase');
      if (stored) return stored;
    } catch (error) {
      console.warn('Storage indisponível para apiBase:', error);
    }

    const datasetBase = document.body?.dataset?.apiBase;
    if (datasetBase) return datasetBase;

    return '';
  }

  function buildUrl(path) {
    const base = window.__DIVINO_FORCE_API_BASE__ || resolveStoredApiBase();
    const normalised = normalisePath(path);
    if (!base) return normalised;
    return `${base.replace(/\/+$/, '')}${normalised}`;
  }

  function cloneFallback(fallback) {
    if (Array.isArray(fallback)) {
      return fallback.map((item) => (item && typeof item === 'object' ? { ...item } : item));
    }
    if (fallback && typeof fallback === 'object') {
      return { ...fallback };
    }
    return fallback;
  }

  async function fetchJSON(path, fallback) {
    const url = buildUrl(path);
    try {
      const response = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.status = response.status;
        throw error;
      }
      const data = await response.json();
      fallbackUsage.delete(path);
      return data;
    } catch (error) {
      console.warn(`Falha ao carregar ${path}:`, error?.message || error);
      if (typeof fallback !== 'undefined') {
        fallbackUsage.add(path);
        return cloneFallback(fallback);
      }
      throw error;
    }
  }

  async function postJSON(path, payload) {
    const url = buildUrl(path);
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Falha ao enviar (${response.status})`);
      }
      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError') {
        throw new Error('Não foi possível conectar à API. Garanta que o servidor neon está no ar.');
      }
      throw error;
    }
  }

  function usingFallback(path) {
    return fallbackUsage.has(path);
  }

  const tracksFallback = trackNames.map((name, index) => ({
    track_name: name,
    votos: 0,
    position: index + 1
  }));

  window.DIVINO = {
    get apiBase() {
      const base = buildUrl('/').replace(/\/$/, '');
      return base === '' ? '' : base;
    },
    resolveApiPath: buildUrl,
    eventsFallback,
    trackNames,
    tracksFallback,
    fetchJSON,
    postJSON,
    usingFallback
  };
})();
