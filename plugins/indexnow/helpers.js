import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const HOST = 'rackmath.com';
const SITE_ID = 'cd170452-ca6f-42b7-a117-349ff9f4dba1';
const STATE_PATH = '.netlify/indexnow-state.json';
const MANIFEST_PATH = '.netlify/indexnow-manifest.json';
const ENDPOINT = 'https://api.indexnow.org/indexnow';
const FIRST_SUBMISSION = [
  'https://rackmath.com/',
  'https://rackmath.com/tools/',
  'https://rackmath.com/tools/barbell-calculator',
];
const MAX_BATCH = 10_000;

// Only these deliberate messages may reach build logs. Native network errors can
// contain the ownership-key URL, so their message/body must never be logged.
class SubmissionError extends Error {}

function validateSnapshot(value) {
  if (!value || value.version !== 1 || value.host !== HOST ||
      !value.pages || typeof value.pages !== 'object' || Array.isArray(value.pages)) {
    throw new SubmissionError('Invalid page manifest or cached state; no URLs submitted.');
  }
  for (const [location, digest] of Object.entries(value.pages)) {
    let url;
    try {
      url = new URL(location);
    } catch {
      throw new SubmissionError('Unsafe canonical URL in manifest or cached state; no URLs submitted.');
    }
    if (url.protocol !== 'https:' || url.host !== HOST || url.username || url.password ||
        url.href !== location || location.includes('?') || location.includes('#') ||
        typeof digest !== 'string' || !/^[0-9a-f]{64}$/.test(digest)) {
      throw new SubmissionError('Unsafe canonical URL or digest in manifest or cached state; no URLs submitted.');
    }
  }
  return value;
}

async function readSnapshot(path, optional = false) {
  let contents;
  try {
    contents = await readFile(path, 'utf8');
  } catch (error) {
    if (optional && error.code === 'ENOENT') return null;
    throw new SubmissionError('Cannot read page manifest or cached state; no URLs submitted.');
  }
  try {
    return validateSnapshot(JSON.parse(contents));
  } catch (error) {
    if (error instanceof SubmissionError) throw error;
    throw new SubmissionError('Invalid JSON in page manifest or cached state; no URLs submitted.');
  }
}

async function writeSnapshot(path, snapshot) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp`;
  try {
    await writeFile(temporary, JSON.stringify(snapshot), 'utf8');
    await rename(temporary, path);
  } finally {
    await rm(temporary, { force: true });
  }
}

export function createIndexNowHooks({
  env = process.env,
  cwd = process.cwd(),
  fetchImpl = globalThis.fetch,
  logger = console,
  timeoutMs = 15_000,
} = {}) {
  let cacheReady = false;
  const statePath = resolve(cwd, STATE_PATH);
  const manifestPath = resolve(cwd, MANIFEST_PATH);
  const isProduction = (constants) => env.CONTEXT === 'production' && env.BRANCH === 'main' &&
    constants?.SITE_ID === SITE_ID && constants?.IS_LOCAL === false;

  function report(utils, summary, warning = false) {
    (warning ? logger.warn : logger.log)(`IndexNow: ${summary}`);
    // Reporting failures must never affect a deployed site or leak native errors.
    try {
      utils.status?.show({ title: 'IndexNow', summary });
    } catch {
      logger.warn('IndexNow: Could not update the deploy summary.');
    }
  }

  async function request(url, options, consume) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(url, {
        ...options,
        redirect: 'error',
        signal: controller.signal,
      });
      return await consume(response);
    } catch (error) {
      if (error instanceof SubmissionError) throw error;
      throw new SubmissionError('Network request failed or timed out; submission state unchanged. Retry on the next production deployment.');
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    async onPreBuild({ constants, utils }) {
      cacheReady = false;
      if (!isProduction(constants)) return;
      try {
        // No digests or TTL: content is updated only after an acknowledged batch.
        await utils.cache.restore(STATE_PATH, { cwd });
        cacheReady = true;
      } catch {
        report(utils, 'Could not restore submission state; automatic submission skipped for this deployment.', true);
      }
    },

    async onSuccess({ constants, utils }) {
      if (!isProduction(constants)) {
        report(utils, 'Skipped: automatic submission runs only on remote production main deployments for rackmath.com.');
        return;
      }
      if (!cacheReady) {
        report(utils, 'Submission state was not restored; automatic submission skipped for this deployment.', true);
        return;
      }
      try {
        const current = await readSnapshot(manifestPath);
        const previous = await readSnapshot(statePath, true);
        const changed = previous
          ? Object.keys(current.pages).filter((url) => previous.pages[url] !== current.pages[url])
          : FIRST_SUBMISSION.filter((url) => Object.hasOwn(current.pages, url));
        const deleted = previous
          ? Object.keys(previous.pages).filter((url) => !Object.hasOwn(current.pages, url))
          : [];
        const urls = [...changed, ...deleted];

        if (previous && urls.length === 0) {
          report(utils, 'No page content changes; no URLs submitted.');
          return;
        }
        if (urls.length === 0) {
          throw new SubmissionError('Initial manifest has no eligible recent URLs; no URLs submitted or baseline saved.');
        }

        const key = (env.INDEXNOW_KEY || '').trim();
        if (!/^[0-9a-f]{32}$/.test(key)) {
          throw new SubmissionError('INDEXNOW_KEY is missing or invalid; automatic submission skipped.');
        }
        const keyLocation = `https://${HOST}/${key}.txt`;
        await request(keyLocation, { headers: { 'Cache-Control': 'no-cache' } }, async (response) => {
          if (response.status !== 200 || await response.text() !== key) {
            throw new SubmissionError('Live ownership file does not match the configured key; submission state unchanged.');
          }
        });

        const statuses = [];
        for (let index = 0; index < urls.length; index += MAX_BATCH) {
          const status = await request(ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
            body: JSON.stringify({ host: HOST, key, keyLocation, urlList: urls.slice(index, index + MAX_BATCH) }),
          }, async (response) => {
            if (response.status !== 200 && response.status !== 202) {
              throw new SubmissionError(`Submission returned HTTP ${response.status}; state unchanged. Retry on the next production deployment.`);
            }
            return response.status;
          });
          statuses.push(status);
        }

        const pending = statuses.includes(202);
        const snapshot = {
          version: 1,
          host: HOST,
          pages: current.pages,
          receipt: pending ? 'key-validation-pending' : 'received',
        };
        try {
          await writeSnapshot(statePath, snapshot);
          if (!await utils.cache.save(STATE_PATH, { cwd })) throw new Error('Cache save failed');
        } catch {
          // Keep the local state at the previous acknowledgement when saving
          // fails, so a later build retries instead of silently losing updates.
          if (previous) await writeSnapshot(statePath, previous);
          else await rm(statePath, { force: true });
          throw new SubmissionError('Submission received, but saving state failed; a later production deployment may repeat these URLs.');
        }
        const receipt = pending ? 'HTTP 202: key validation pending' : 'HTTP 200: received';
        const baseline = previous ? '' : ' Initial baseline saved; older pages were not bulk-submitted.';
        report(utils, `${urls.length} URL(s) submitted (${deleted.length} removed). ${receipt}. This does not confirm indexing.${baseline}`);
      } catch (error) {
        report(utils, error instanceof SubmissionError ? error.message : 'Automatic submission could not complete; retry on the next production deployment.', true);
      }
    },
  };
}
