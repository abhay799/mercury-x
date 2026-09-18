const entityMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => entityMap[char]);

const slug = (value) => String(value ?? 'unknown').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

export const chip = (label, tone = label) => `
  <span class="chip chip--${slug(tone)}"><span class="chip__mark" aria-hidden="true"></span>${escapeHtml(label)}</span>`;

export const provenanceBadge = (provenance) => {
  const source = provenance?.sourceType ?? 'UNKNOWN';
  const evidence = provenance?.evidenceState ?? 'UNKNOWN';
  return `<span class="provenance provenance--${slug(source)}" title="Evidence: ${escapeHtml(evidence)} · Calibration: ${escapeHtml(provenance?.calibrationState ?? 'UNKNOWN')}">
    <span aria-hidden="true">◆</span> ${escapeHtml(source)}
  </span>`;
};

export const pageHeader = (eyebrow, title, description, provenance) => `
  <header class="page-header">
    <div><p class="eyebrow">${escapeHtml(eyebrow)}</p><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></div>
    ${provenance ? provenanceBadge(provenance) : ''}
  </header>`;

export const panel = (title, body, options = {}) => `
  <section class="panel ${options.className ?? ''}">
    <header class="panel__header"><div><p class="panel__eyebrow">${escapeHtml(options.eyebrow ?? '')}</p><h2>${escapeHtml(title)}</h2></div>${options.action ?? ''}</header>
    <div class="panel__body">${body}</div>
  </section>`;

export const metricCard = (metric) => `
  <article class="metric-card">
    <div class="metric-card__top"><span>${escapeHtml(metric.label)}</span>${provenanceBadge(metric.provenance)}</div>
    <strong>${escapeHtml(metric.value)}</strong>
    <p>${escapeHtml(metric.detail)}</p>
  </article>`;

export const definitionList = (rows) => `<dl class="definition-list">${rows.map(([term, detail]) => `
  <div><dt>${escapeHtml(term)}</dt><dd>${escapeHtml(detail)}</dd></div>`).join('')}</dl>`;

export const table = (headers, rows, options = {}) => `
  <div class="table-wrap"><table class="data-table ${options.compact ? 'data-table--compact' : ''}">
    <thead><tr>${headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody>
  </table></div>`;

export const progress = (value, max, label) => {
  const percent = Math.max(0, Math.min(100, (Number(value) / Number(max)) * 100));
  return `<div class="progress"><div class="progress__labels"><span>${escapeHtml(label)}</span><span>${escapeHtml(value)} / ${escapeHtml(max)}</span></div><div class="progress__track"><span style="width:${percent}%"></span></div></div>`;
};

export const provenanceDetail = (provenance) => panel('Evidence provenance', `
  ${definitionList([
    ['Source type', provenance?.sourceType ?? 'UNKNOWN'],
    ['Evidence state', provenance?.evidenceState ?? 'UNKNOWN'],
    ['Calibration', provenance?.calibrationState ?? 'UNKNOWN'],
    ['Generated at', provenance?.generatedAt ?? 'UNKNOWN'],
  ])}
  <div class="tag-list">${(provenance?.sourceIds ?? []).map((id) => `<span class="tag">${escapeHtml(id)}</span>`).join('') || '<span class="muted">No source identifiers supplied.</span>'}</div>
`, { eyebrow: 'TRACEABILITY' });

export const emptyState = (title, message) => `<div class="empty-state"><span aria-hidden="true">◇</span><h2>${escapeHtml(title)}</h2><p>${escapeHtml(message)}</p></div>`;

export const callout = (title, text, tone = 'info') => `<aside class="callout callout--${slug(tone)}"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p></aside>`;
