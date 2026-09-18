import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const artifactRoot = path.join(repoRoot, 'dist', 'pages');
const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

function exists(relativePath) {
  return fs.existsSync(path.join(artifactRoot, relativePath));
}

function read(relativePath) {
  const absolutePath = path.join(artifactRoot, relativePath);
  try {
    return fs.readFileSync(absolutePath, 'utf8');
  } catch {
    failures.push(`missing or unreadable artifact file: ${relativePath}`);
    return '';
  }
}

function localHrefTargets(html) {
  return [...html.matchAll(/href="([^"]+)"/g)]
    .map((match) => match[1])
    .filter((href) => !href.startsWith('#') && !/^(?:https?:|mailto:)/.test(href));
}

function resolveArtifactTarget(fromRelativePath, target) {
  return path.resolve(path.dirname(path.join(artifactRoot, fromRelativePath)), target.split('#', 1)[0]);
}

function isInsideArtifact(target) {
  return target === artifactRoot || target.startsWith(`${artifactRoot}${path.sep}`);
}

function collectJavaScript(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...collectJavaScript(target));
    else if (entry.isFile() && entry.name.endsWith('.js')) files.push(target);
  }
  return files;
}

function assertRelativeModuleImportsResolve() {
  const sourceRoot = path.join(artifactRoot, 'control-center', 'src');
  if (!fs.existsSync(sourceRoot)) return;
  for (const sourceFile of collectJavaScript(sourceRoot)) {
    const source = fs.readFileSync(sourceFile, 'utf8');
    for (const match of source.matchAll(/\bfrom\s+['"]([^'"]+)['"]/g)) {
      const specifier = match[1];
      if (!specifier.startsWith('.')) continue;
      const resolved = path.resolve(path.dirname(sourceFile), specifier);
      assert(isInsideArtifact(resolved), `module import escapes artifact: ${path.relative(artifactRoot, sourceFile)} -> ${specifier}`);
      assert(fs.existsSync(resolved), `missing module import target: ${path.relative(artifactRoot, sourceFile)} -> ${specifier}`);
    }
  }
}

for (const required of [
  'index.html',
  'styles.css',
  'app.js',
  'control-center/index.html',
  'control-center/styles.css',
  'control-center/src',
  'docs',
  'README.md',
  '.nojekyll',
]) {
  assert(exists(required), `missing required artifact path: ${required}`);
}

const portfolioHtml = read('index.html');
const controlHtml = read('control-center/index.html');
const portfolioJavaScript = read('app.js');
const controlData = read('control-center/src/data/demo-data.js');
const scenarioDefinitions = read('control-center/src/scenarios/definitions.js');

assert(!portfolioHtml.includes('../control-center'), 'copied Portfolio retains ../control-center link');
assert(!portfolioHtml.includes('../../docs'), 'copied Portfolio retains ../../docs link');
assert(!portfolioHtml.includes('../../README.md'), 'copied Portfolio retains ../../README.md link');
assert(portfolioHtml.includes('href="control-center/index.html"'), 'Portfolio does not link to the Control Center artifact');

for (const href of localHrefTargets(portfolioHtml)) {
  const target = resolveArtifactTarget('index.html', href);
  assert(isInsideArtifact(target), `Portfolio link escapes artifact: ${href}`);
  assert(fs.existsSync(target), `Portfolio link target is missing: ${href}`);
}

for (const [file, content] of [
  ['index.html', portfolioHtml],
  ['app.js', portfolioJavaScript],
  ['control-center/index.html', controlHtml],
]) {
  assert(!/(?:href|src)="\//.test(content), `root-absolute HTML path introduced in ${file}`);
}

for (const stylesheet of ['styles.css', 'control-center/styles.css']) {
  assert(!/url\(\s*['"]?\//.test(read(stylesheet)), `root-absolute CSS path introduced in ${stylesheet}`);
}

assertRelativeModuleImportsResolve();
assert(!/provenance\(\s*['"]LIVE['"]/.test(controlData), 'demo data emits LIVE provenance');
assert(!/provenance\(\s*['"]LIVE['"]/.test(scenarioDefinitions), 'scenario data emits LIVE provenance');
assert(!/"sourceType"\s*:\s*"LIVE"/.test(`${controlData}\n${scenarioDefinitions}`), 'static data serializes LIVE provenance');

for (const phrase of [
  'Research / Experimental',
  'STATIC_DEMO',
  'SYNTHETIC',
  'SIMULATED',
  'UNCALIBRATED',
  'NOT_MEASURED',
  'production datacenter deployment',
  'production GPU runtime',
]) {
  assert(portfolioHtml.includes(phrase), `Portfolio boundary language missing: ${phrase}`);
}
for (const phrase of ['STATIC DEMO', 'No live infrastructure', 'No production runtime connected']) {
  assert(controlHtml.includes(phrase), `Control Center boundary language missing: ${phrase}`);
}

const allowedRootEntries = new Set(['.nojekyll', 'README.md', 'app.js', 'control-center', 'docs', 'index.html', 'styles.css']);
if (fs.existsSync(artifactRoot)) {
  for (const entry of fs.readdirSync(artifactRoot)) {
    assert(allowedRootEntries.has(entry), `unexpected artifact root entry: ${entry}`);
  }
}
for (const prohibited of ['.git', '.venv', 'artifacts/evidence', 'tests', 'src', 'ui']) {
  assert(!exists(prohibited), `prohibited repository content copied into artifact: ${prohibited}`);
}

if (failures.length) {
  console.error(failures.map((failure) => `FAIL: ${failure}`).join('\n'));
  process.exit(1);
}

console.log('PASS: GitHub Pages artifact layout, links, modules, provenance, and claim boundaries validated');
