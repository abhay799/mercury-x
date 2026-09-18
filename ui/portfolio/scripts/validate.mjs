import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const portfolioRoot = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(portfolioRoot, "..", "..");

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

function read(relativePath) {
  const absolutePath = path.join(portfolioRoot, relativePath);
  requireCondition(fs.existsSync(absolutePath), `missing portfolio file: ${relativePath}`);
  return fs.readFileSync(absolutePath, "utf8");
}

const html = read("index.html");
const css = read("styles.css");
const javascript = read("app.js");

const requiredSections = [
  "problem",
  "architecture",
  "lifecycle",
  "systems",
  "safety",
  "scenarios",
  "evidence",
  "boundaries",
  "technology",
  "status",
];

for (const section of requiredSections) {
  requireCondition(html.includes(`id="${section}"`), `missing portfolio section: ${section}`);
}

for (const phrase of [
  "MERCURY X",
  "Autonomous AI Compute &amp; Inference Fabric",
  "Research / Experimental",
  "Control-Plane Architecture",
  "Launch Control Center",
  "1506",
  "256",
  "six deterministic scenarios",
  "STATIC_DEMO",
  "SYNTHETIC",
  "SIMULATED",
  "UNCALIBRATED",
  "NOT_MEASURED",
]) {
  requireCondition(html.includes(phrase), `missing required evidence or boundary text: ${phrase}`);
}

requireCondition((html.match(/class="scenario-card"/g) ?? []).length === 6, "expected six scenario cards");
requireCondition((html.match(/class="layer-card"/g) ?? []).length === 9, "expected nine architecture layer cards");
requireCondition(html.includes("<main id=\"main-content\""), "semantic main landmark missing");
requireCondition(html.includes("class=\"skip-link\""), "skip link missing");
requireCondition(html.includes("aria-label=\"Primary navigation\""), "navigation label missing");

const localLinks = [...html.matchAll(/href="([^"]+)"/g)]
  .map((match) => match[1])
  .filter((href) => !href.startsWith("#") && !href.startsWith("http:") && !href.startsWith("https:") && !href.startsWith("mailto:"));

requireCondition(localLinks.length >= 5, "portfolio must link to repository evidence and product surfaces");
for (const href of localLinks) {
  const target = path.resolve(portfolioRoot, href.split("#", 1)[0]);
  requireCondition(target.startsWith(repoRoot), `link escapes repository: ${href}`);
  requireCondition(fs.existsSync(target), `broken local link: ${href}`);
}

requireCondition(css.includes("@media"), "responsive styles missing");
requireCondition(css.includes(":focus-visible"), "keyboard focus styles missing");
requireCondition(css.includes("prefers-reduced-motion"), "reduced-motion support missing");
requireCondition(javascript.includes("aria-expanded"), "accessible navigation behavior missing");
requireCondition(!javascript.includes("fetch("), "portfolio must not fetch live data");

const combined = `${html}\n${css}\n${javascript}`;
requireCondition(!/\b(TODO|TBD|PLACEHOLDER)\b/i.test(combined), "placeholder content present");
requireCondition(!/LIVE[_ -]?TELEMETRY/i.test(combined), "fake live telemetry claim present");
requireCondition(!/https?:\/\//i.test(combined), "external assets or hosted URL present");

const evidence = fs.readFileSync(path.join(repoRoot, "docs", "evidence", "BENCHMARKS_AND_EVIDENCE.md"), "utf8");
for (const value of ["1506 passed", "256 passed", "six deterministic scenarios"]) {
  requireCondition(evidence.includes(value), `portfolio evidence is not grounded in committed report: ${value}`);
}

const readme = fs.readFileSync(path.join(repoRoot, "README.md"), "utf8");
requireCondition(readme.includes("ui/portfolio/"), "README does not link to portfolio");

console.log("PASS: portfolio structure and nine-layer architecture validated");
console.log("PASS: six scenarios and committed evidence values validated");
console.log(`PASS: ${localLinks.length} internal repository links resolved`);
console.log("PASS: accessibility, provenance, and claim boundaries validated");
process.exit(0);
