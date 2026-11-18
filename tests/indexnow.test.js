import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { createIndexNowHooks } from '../plugins/indexnow/helpers.js';

const KEY = '0123456789abcdef0123456789abcdef';
const HASH_A = 'a'.repeat(64);
const HASH_B = 'b'.repeat(64);
const INITIAL = ['https://rackmath.com/', 'https://rackmath.com/tools/', 'https://rackmath.com/tools/barbell-calculator'];
const OLD_URL = 'https://rackmath.com/blog/existing-article';
const PAGES = Object.fromEntries([...INITIAL, OLD_URL].map((url) => [url, HASH_A]));
const snapshot = (pages) => ({ version: 1, host: 'rackmath.com', pages });

async function fixture(t, { previous, pages = PAGES, env = {}, constants = {}, restoreError = false, saveError = false, respond } = {}) {
  const cwd = await mkdtemp(join(tmpdir(), 'rackmath-indexnow-'));
  t.after(() => rm(cwd, { recursive: true, force: true }));
  await mkdir(join(cwd, '.netlify'));
  const manifestPath = join(cwd, '.netlify/indexnow-manifest.json');
  const statePath = join(cwd, '.netlify/indexnow-state.json');
  await writeFile(manifestPath, JSON.stringify(snapshot(pages)));
  let cached = previous ? JSON.stringify(previous) : null;
  const calls = [];
  const summaries = [];
  const logs = [];
  let saves = 0;
  let restores = 0;
  const args = {
    constants: { SITE_ID: 'cd170452-ca6f-42b7-a117-349ff9f4dba1', IS_LOCAL: false, ...constants },
    utils: {
      cache: {
        async restore(path, options) {
          restores++;
          assert.equal(path, '.netlify/indexnow-state.json');
          assert.equal(options.cwd, cwd);
          if (restoreError) throw new Error('restore unavailable');
          if (cached === null) return false;
          await writeFile(statePath, cached);
          return true;
        },
        async save(path, options) {
          saves++;
          assert.equal(path, '.netlify/indexnow-state.json');
          assert.equal(options.cwd, cwd);
          if (saveError) throw new Error('save unavailable');
          cached = await readFile(statePath, 'utf8');
          return true;
        },
      },
      status: { show: ({ summary }) => summaries.push(summary) },
    },
  };
  const hooks = createIndexNowHooks({
    cwd,
    env: { CONTEXT: 'production', BRANCH: 'main', INDEXNOW_KEY: KEY, ...env },
    logger: { log: (message) => logs.push(message), warn: (message) => logs.push(message) },
    timeoutMs: 25,
    fetchImpl: async (url, options) => {
      calls.push({ url, ...options });
      assert.equal(options.redirect, 'error');
      return respond ? respond(url, options) : new Response(options.method === 'POST' ? '' : KEY, { status: 200 });
    },
  });
  t.after(() => assert.equal(logs.join('\n').includes(KEY), false, 'ownership key must never reach logs'));
  return {
    args, hooks, calls, summaries, statePath,
    get saves() { return saves; },
    get restores() { return restores; },
    get cached() { return cached && JSON.parse(cached); },
    async update(pages) { await writeFile(manifestPath, JSON.stringify(snapshot(pages))); },
    async run() { await hooks.onPreBuild(args); await hooks.onSuccess(args); },
  };
}

test('first production deployment submits only three recent URLs and seeds all pages', async (t) => {
  const f = await fixture(t);
  await f.run();
  assert.equal(f.calls.length, 2);
  assert.equal(f.calls[0].url, `https://rackmath.com/${KEY}.txt`);
  const payload = JSON.parse(f.calls[1].body);
  assert.equal(f.calls[1].url, 'https://api.indexnow.org/indexnow');
  assert.equal(payload.host, 'rackmath.com');
  assert.equal(payload.key, KEY);
  assert.equal(payload.keyLocation, f.calls[0].url);
  assert.deepEqual(payload.urlList, INITIAL);
  assert.deepEqual(f.cached.pages, PAGES);
  assert.equal(f.cached.receipt, 'received');
  assert.equal(f.saves, 1);
  assert.match(f.summaries.at(-1), /HTTP 200: received.*does not confirm indexing/);
});

test('preview, branch, local, unknown-local and other-site deployments do no work', async (t) => {
  for (const options of [
    { env: { CONTEXT: 'deploy-preview' } },
    { env: { CONTEXT: 'branch-deploy' } },
    { env: { BRANCH: 'feature' } },
    { constants: { IS_LOCAL: true } },
    { constants: { IS_LOCAL: undefined } },
    { constants: { SITE_ID: 'another-site' } },
  ]) {
    const f = await fixture(t, options);
    await f.run();
    assert.equal(f.calls.length, 0);
    assert.equal(f.restores, 0);
    assert.equal(f.saves, 0);
  }
});

test('unchanged content produces no network requests or new cached state', async (t) => {
  const f = await fixture(t, { previous: snapshot(PAGES) });
  await f.run();
  assert.equal(f.calls.length, 0);
  assert.equal(f.saves, 0);
  assert.match(f.summaries.at(-1), /No page content changes/);
});

test('subsequent deployment submits added, changed and deleted canonical URLs', async (t) => {
  const added = 'https://rackmath.com/tools/new-calculator';
  const pages = { ...PAGES, [INITIAL[0]]: HASH_B, [added]: HASH_A };
  delete pages[OLD_URL];
  const f = await fixture(t, { previous: snapshot(PAGES), pages });
  await f.run();
  assert.deepEqual(JSON.parse(f.calls[1].body).urlList, [INITIAL[0], added, OLD_URL]);
  assert.deepEqual(f.cached.pages, pages);
  assert.match(f.summaries.at(-1), /3 URL\(s\) submitted \(1 removed\)/);
});

test('rejects hostile URL scope and invalid hashes in current manifest or saved state', async (t) => {
  const hostile = [
    'https://rackmath.app/', 'https://preview--rackmath.netlify.app/',
    'http://rackmath.com/', 'https://www.rackmath.com/',
    'https://rackmath.com:443/', 'https://rackmath.com/?q=1',
    'https://rackmath.com/#section', 'https://rackmath.com/?',
    'https://rackmath.com/#', 'https://user@rackmath.com/',
    'https://rackmath.com/tools/../',
  ];
  for (const url of hostile) {
    for (const source of ['current', 'previous']) {
      const pages = { ...PAGES, [url]: HASH_A };
      const f = await fixture(t, source === 'current' ? { pages } : { previous: snapshot(pages) });
      await f.run();
      assert.equal(f.calls.length, 0, `${source}: ${url}`);
      assert.equal(f.saves, 0);
    }
  }
  for (const invalid of ['bad-hash', [HASH_A], null]) {
    const f = await fixture(t, { pages: { ...PAGES, [INITIAL[0]]: invalid } });
    await f.run();
    assert.equal(f.calls.length, 0);
  }
});

test('failed POST preserves acknowledgement, retries next deployment, then skips unchanged content', async (t) => {
  let status = 429;
  const pages = { ...PAGES, [INITIAL[0]]: HASH_B };
  const f = await fixture(t, {
    previous: snapshot(PAGES), pages,
    respond: (_, options) => new Response(options.method === 'POST' ? '' : KEY, { status: options.method === 'POST' ? status : 200 }),
  });
  await f.run();
  assert.equal(f.calls.length, 2, 'no immediate retry loop');
  assert.deepEqual(f.cached.pages, PAGES);
  assert.equal(f.saves, 0);
  assert.match(f.summaries.at(-1), /HTTP 429; state unchanged/);
  status = 200;
  await f.run();
  assert.deepEqual(JSON.parse(f.calls[3].body).urlList, [INITIAL[0]]);
  assert.deepEqual(f.cached.pages, pages);
  await f.run();
  assert.equal(f.calls.length, 4);
});

test('202 records pending key validation without claiming indexing', async (t) => {
  const f = await fixture(t, {
    respond: (_, options) => new Response(options.method === 'POST' ? '' : KEY, { status: options.method === 'POST' ? 202 : 200 }),
  });
  await f.run();
  assert.equal(f.cached.receipt, 'key-validation-pending');
  assert.match(f.summaries.at(-1), /HTTP 202: key validation pending.*does not confirm indexing/);
});

test('live key mismatch, unavailable file, or redirect stops before submission', async (t) => {
  for (const response of [new Response('wrong-key'), new Response(`${KEY}\n`), new Response(KEY, { status: 404 }), new Response('', { status: 301 })]) {
    const f = await fixture(t, { respond: () => response });
    await f.run();
    assert.equal(f.calls.length, 1);
    assert.equal(f.saves, 0);
    assert.equal(f.cached, null);
    assert.match(f.summaries.at(-1), /Live ownership file does not match/);
  }
});

test('invalid or missing configured key does not fetch', async (t) => {
  for (const key of ['', 'invalid', KEY.toUpperCase()]) {
    const f = await fixture(t, { env: { INDEXNOW_KEY: key } });
    await f.run();
    assert.equal(f.calls.length, 0);
    assert.equal(f.saves, 0);
  }
});

test('network failures and timeouts are nonblocking and do not disclose keys', async (t) => {
  for (const respond of [
    (url) => { throw new Error(`Cannot connect to ${url}`); },
    (_, { signal }) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('timeout')), { once: true })),
  ]) {
    const f = await fixture(t, { respond });
    await f.run();
    assert.equal(f.saves, 0);
    assert.equal(f.cached, null);
    assert.match(f.summaries.at(-1), /failed or timed out/);
  }
});

test('cache restore failure prevents submission, and cache save failure keeps old state', async (t) => {
  const restore = await fixture(t, { restoreError: true });
  await restore.run();
  assert.equal(restore.calls.length, 0);
  const previous = snapshot(PAGES);
  const save = await fixture(t, { previous, pages: { ...PAGES, [INITIAL[0]]: HASH_B }, saveError: true });
  await save.run();
  assert.deepEqual(save.cached, previous);
  assert.deepEqual(JSON.parse(await readFile(save.statePath, 'utf8')), previous);
  assert.match(save.summaries.at(-1), /saving state failed/);
});
