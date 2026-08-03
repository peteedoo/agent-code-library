'use strict';

const $ = (id) => document.getElementById(id);
const state = { q: '', category: '', language: '' };
let debounce;

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function repoCard(r) {
  return `<a class="card" href="${esc(r.url)}" target="_blank" rel="noopener">
    <div class="top">
      <span class="name">${esc(r.name)}</span>
      <span class="owner">${esc(r.owner)}/</span>
    </div>
    <div class="desc">${esc(r.description)}</div>
    <div class="tags">
      <span class="tag">${esc(r.category)}</span>
      <span class="tag lang">${esc(r.language)}</span>
    </div>
  </a>`;
}

async function render() {
  const qs = new URLSearchParams();
  if (state.q) qs.set('q', state.q);
  if (state.category) qs.set('category', state.category);
  if (state.language) qs.set('language', state.language);
  const data = await api('/api/repos?' + qs.toString());
  $('count').textContent = `${data.count} repo${data.count === 1 ? '' : 's'}`;
  $('results').innerHTML = data.repos.length
    ? data.repos.map(repoCard).join('')
    : '<div class="empty">no repos match your filters</div>';
}

async function initFilters() {
  const { categories, languages } = await api('/api/categories');
  for (const c of categories) {
    $('category').insertAdjacentHTML('beforeend', `<option value="${esc(c)}">${esc(c)}</option>`);
  }
  for (const l of languages) {
    $('language').insertAdjacentHTML('beforeend', `<option value="${esc(l)}">${esc(l)}</option>`);
  }
}

$('search').addEventListener('input', (e) => {
  clearTimeout(debounce);
  debounce = setTimeout(() => { state.q = e.target.value; render(); }, 120);
});
$('category').addEventListener('change', (e) => { state.category = e.target.value; render(); });
$('language').addEventListener('change', (e) => { state.language = e.target.value; render(); });

initFilters().then(render);
