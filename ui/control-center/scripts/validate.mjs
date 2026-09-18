import { spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DemoControlCenterProvider } from '../src/data/demo-provider.js';
import { SOURCE_TYPES } from '../src/types.js';
import { renderView, VIEW_DEFINITIONS } from '../src/views.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const required = [
  'index.html', 'styles.css', 'src/app.js', 'src/components.js', 'src/views.js',
  'src/types.js', 'src/data/provider.js', 'src/data/demo-provider.js', 'src/data/demo-data.js',
];

const failures = [];
const assert = (condition, message) => { if (!condition) failures.push(message); };

for (const relative of required) {
  try { assert((await stat(path.join(root, relative))).isFile(), `Missing file: ${relative}`); }
  catch { failures.push(`Missing file: ${relative}`); }
}

const sourceFiles = [];
async function collect(directory) {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const target = path.join(directory, item.name);
    if (item.isDirectory()) await collect(target);
    else if (item.name.endsWith('.js')) sourceFiles.push(target);
  }
}
await collect(path.join(root, 'src'));
for (const file of sourceFiles) {
  const result = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
  assert(result.status === 0, `JavaScript syntax failed: ${path.relative(root, file)}\n${result.stderr}`);
}

const html = await readFile(path.join(root, 'index.html'), 'utf8');
const css = await readFile(path.join(root, 'styles.css'), 'utf8');
const views = await readFile(path.join(root, 'src/views.js'), 'utf8');
assert(html.includes('src/app.js') && html.includes('styles.css'), 'HTML entrypoint references are incomplete');
assert((css.match(/{/g) ?? []).length === (css.match(/}/g) ?? []).length, 'CSS braces are unbalanced');
assert((views.match(/\['[a-z-]+', '[^']+', '[^']+'\]/g) ?? []).length === 14, 'Expected 14 navigation view definitions');

const snapshot = await new DemoControlCenterProvider().getSnapshot();
assert(snapshot.schema === 'mercury.control-center/v1', 'Unexpected control-center schema');
assert(snapshot.mode === 'STATIC DEMONSTRATION', 'Demo provider must declare demonstration mode');
assert(snapshot.workloads.length > 0 && snapshot.evidence.length > 0, 'Demo snapshot lacks required artifacts');
assert(VIEW_DEFINITIONS.length === 14, 'Expected fourteen discoverable control-center views');
for (const [viewId, label] of VIEW_DEFINITIONS) {
  const markup = renderView(viewId, snapshot, { selectedWorkload: snapshot.workloads[0].id });
  assert(typeof markup === 'string' && markup.length > 500, `View did not render meaningful markup: ${label}`);
  assert(markup.includes('<h1>'), `View lacks a primary heading: ${label}`);
}

let provenanceCount = 0;
const observedSourceTypes = new Set();
function inspect(value, trail = 'snapshot') {
  if (!value || typeof value !== 'object') return;
  if ('provenance' in value) {
    provenanceCount += 1;
    const item = value.provenance;
    if (item) observedSourceTypes.add(item.sourceType);
    assert(item && SOURCE_TYPES.includes(item.sourceType), `Invalid provenance source at ${trail}`);
    assert(item?.generatedAt && item?.evidenceState && item?.calibrationState, `Incomplete provenance at ${trail}`);
  }
  for (const [key, child] of Object.entries(value)) inspect(child, `${trail}.${key}`);
}
inspect(snapshot);
assert(provenanceCount >= 30, 'Expected broad provenance coverage in demo data');
assert(!observedSourceTypes.has('LIVE'), 'Static demo provider must never emit LIVE provenance');
assert(!JSON.stringify(snapshot).includes('AUTO_DEGRADE'), 'Forbidden automatic quality degradation marker found');
assert(snapshot.scheduler.policy.promoted === false, 'Demo policy must not be autonomously promoted');
assert(snapshot.twin.calibration === 'UNCALIBRATED' && snapshot.twin.status === 'ADVISORY', 'Twin boundary is not explicit');
assert(snapshot.migration.authority.authoritativeCount === 1, 'Migration authority invariant failed');

const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript' };
const server = createServer(async (request, response) => {
  const relative = request.url === '/' ? 'index.html' : request.url.replace(/^\//, '');
  const resolved = path.resolve(root, relative);
  if (!resolved.startsWith(root)) { response.writeHead(403).end(); return; }
  try {
    const body = await readFile(resolved);
    response.writeHead(200, { 'content-type': mime[path.extname(resolved)] ?? 'application/octet-stream' });
    response.end(body);
  } catch { response.writeHead(404).end(); }
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
try {
  const port = server.address().port;
  for (const target of ['/', '/styles.css', '/src/app.js', '/src/data/demo-data.js']) {
    const response = await fetch(`http://127.0.0.1:${port}${target}`);
    assert(response.ok, `Static smoke request failed: ${target}`);
    assert((await response.text()).length > 100, `Static asset unexpectedly empty: ${target}`);
  }
} finally {
  await new Promise((resolve) => server.close(resolve));
}

if (failures.length) {
  console.error(failures.map((failure) => `FAIL: ${failure}`).join('\n'));
  process.exit(1);
}
console.log(`PASS: ${sourceFiles.length} JavaScript modules checked`);
console.log(`PASS: ${VIEW_DEFINITIONS.length} views rendered from the provider contract`);
console.log(`PASS: ${provenanceCount} provenance-bearing demo artifacts validated`);
console.log('PASS: static HTTP smoke test');
