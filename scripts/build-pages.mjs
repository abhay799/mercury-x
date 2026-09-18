import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outputRoot = path.join(repoRoot, 'dist', 'pages');

function requirePath(relativePath, type = 'file') {
  const absolutePath = path.join(repoRoot, relativePath);
  const exists = fs.existsSync(absolutePath);
  const validType = exists && (type === 'directory' ? fs.statSync(absolutePath).isDirectory() : fs.statSync(absolutePath).isFile());
  if (!validType) throw new Error(`required ${type} is missing: ${relativePath}`);
  return absolutePath;
}

function replaceExactHref(html, from, to) {
  const exact = `href="${from}"`;
  const matches = html.match(new RegExp(exact.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) ?? [];
  if (matches.length === 0) throw new Error(`required Portfolio link was not found: ${from}`);
  return html.replaceAll(exact, `href="${to}"`);
}

function copyRequiredFile(sourceRelativePath, destinationRelativePath) {
  const source = requirePath(sourceRelativePath);
  const destination = path.join(outputRoot, destinationRelativePath);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(source, destination);
}

for (const required of [
  ['ui/portfolio/index.html', 'file'],
  ['ui/portfolio/styles.css', 'file'],
  ['ui/portfolio/app.js', 'file'],
  ['ui/control-center', 'directory'],
  ['docs', 'directory'],
  ['README.md', 'file'],
]) {
  requirePath(required[0], required[1]);
}

const relativeOutput = path.relative(repoRoot, outputRoot);
if (!relativeOutput || relativeOutput.startsWith(`..${path.sep}`) || path.isAbsolute(relativeOutput)) {
  throw new Error(`refusing to remove output outside repository: ${outputRoot}`);
}

fs.rmSync(outputRoot, { recursive: true, force: true });
fs.mkdirSync(outputRoot, { recursive: true });

let portfolioHtml = fs.readFileSync(requirePath('ui/portfolio/index.html'), 'utf8');
portfolioHtml = replaceExactHref(portfolioHtml, '../control-center/index.html', 'control-center/index.html');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/architecture/MERCURY_X_ARCHITECTURE.md', 'docs/architecture/MERCURY_X_ARCHITECTURE.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/architecture/PHASE_INDEX.md', 'docs/architecture/PHASE_INDEX.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/architecture/SAFETY_INVARIANTS.md', 'docs/architecture/SAFETY_INVARIANTS.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/ui/DEMO_SCENARIOS.md', 'docs/ui/DEMO_SCENARIOS.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/evidence/BENCHMARKS_AND_EVIDENCE.md', 'docs/evidence/BENCHMARKS_AND_EVIDENCE.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/VALIDATION.md', 'docs/VALIDATION.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../README.md', 'README.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/RUNNING.md', 'docs/RUNNING.md');
portfolioHtml = replaceExactHref(portfolioHtml, '../../docs/LIMITATIONS.md', 'docs/LIMITATIONS.md');

fs.writeFileSync(path.join(outputRoot, 'index.html'), portfolioHtml, 'utf8');
copyRequiredFile('ui/portfolio/styles.css', 'styles.css');
copyRequiredFile('ui/portfolio/app.js', 'app.js');
fs.cpSync(requirePath('ui/control-center', 'directory'), path.join(outputRoot, 'control-center'), { recursive: true });
fs.cpSync(requirePath('docs', 'directory'), path.join(outputRoot, 'docs'), { recursive: true });
copyRequiredFile('README.md', 'README.md');
fs.writeFileSync(path.join(outputRoot, '.nojekyll'), '', 'utf8');

console.log(`PASS: built GitHub Pages artifact at ${path.relative(repoRoot, outputRoot)}`);
process.exit(0);
