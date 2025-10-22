import assert from 'node:assert/strict';
import { fetchJSON, postJSON, API_FALLBACKS, onFallback } from '../public/scripts/api.js';

function restoreFetch(original) {
  if (original === undefined) {
    delete global.fetch;
  } else {
    global.fetch = original;
  }
}

async function testFallbackOnNetworkError() {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('network down');
  };
  try {
    const result = await fetchJSON('/api/events');
    assert.ok(Array.isArray(result), 'resultado deve ser uma lista');
    assert.equal(result.length, API_FALLBACKS['/api/events'].length);
  } finally {
    restoreFetch(originalFetch);
  }
}

async function testFallbackOnHttpError() {
  const originalFetch = global.fetch;
  global.fetch = async () => ({
    ok: false,
    status: 404,
    json: async () => ({ message: 'not found' })
  });
  try {
    const result = await fetchJSON('/api/setlist/top');
    assert.equal(result[0].track_name, API_FALLBACKS['/api/setlist/top'][0].track_name);
  } finally {
    restoreFetch(originalFetch);
  }
}

async function testFallbackNotification() {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('network down');
  };
  let notified = 0;
  const unsubscribe = onFallback(({ path, data }) => {
    notified += 1;
    assert.equal(path, '/api/events');
    assert.ok(Array.isArray(data));
  });
  try {
    await fetchJSON('/api/events');
    assert.equal(notified, 1);
  } finally {
    unsubscribe();
    restoreFetch(originalFetch);
  }
}

async function testPostJSONSuccess() {
  const originalFetch = global.fetch;
  const payload = { track_name: 'ODARA' };
  const responseBody = { ok: true, track: 'ODARA' };
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/setlist/vote');
    assert.equal(options.method, 'POST');
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.equal(options.body, JSON.stringify(payload));
    return {
      ok: true,
      json: async () => responseBody
    };
  };
  try {
    const result = await postJSON('/api/setlist/vote', payload);
    assert.deepEqual(result, responseBody);
  } finally {
    restoreFetch(originalFetch);
  }
}

async function testPostJSONFailure() {
  const originalFetch = global.fetch;
  global.fetch = async () => ({
    ok: false,
    text: async () => 'Falha ao enviar'
  });
  try {
    await assert.rejects(() => postJSON('/api/setlist/vote', {}), {
      message: 'Falha ao enviar'
    });
  } finally {
    restoreFetch(originalFetch);
  }
}

async function run() {
  await testFallbackOnNetworkError();
  await testFallbackOnHttpError();
  await testFallbackNotification();
  await testPostJSONSuccess();
  await testPostJSONFailure();
  console.log('Todos os testes do helper de API passaram.');
}

run().catch((error) => {
  console.error('Teste falhou:', error);
  process.exitCode = 1;
});
