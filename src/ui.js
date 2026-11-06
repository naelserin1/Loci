// HTML templates for menus and overlays.
import { t, getLang, itemName, placeName, roomName } from './i18n.js';

const BASE = import.meta.env.BASE_URL;
export const thumb = (id) => `${BASE}thumbs/${id}.webp`;

export const DIFFICULTIES = {
  easy: { count: 5, loci: [2, 5, 8, 11, 14], options: 10 },
  normal: { count: 10, loci: [1, 3, 4, 6, 7, 9, 10, 12, 13, 15], options: 15 },
  hard: { count: 15, loci: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], options: 20 },
};

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function fmtTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function menuHTML({ difficulty, quality, best }) {
  const diffBtns = Object.entries(DIFFICULTIES).map(([k, d]) => `
    <button class="seg ${k === difficulty ? 'on' : ''}" data-diff="${k}">
      <span>${t(k)}</span><small>${d.count} ${t('objects')}</small>
    </button>`).join('');
  const qBtns = ['low', 'medium', 'high'].map((q) => `
    <button class="seg small ${q === quality ? 'on' : ''}" data-quality="${q}">${t('q_' + q)}</button>`).join('');
  const langBtns = [['es', 'Español'], ['en', 'English']].map(([l, n]) => `
    <button class="seg small ${l === getLang() ? 'on' : ''}" data-lang="${l}">${n}</button>`).join('');
  const b = best[difficulty];
  const controls = t('controls').map(([k, v]) => `<li><kbd>${k}</kbd><span>${v}</span></li>`).join('');
  return `
  <div class="menu">
    <header class="brand">
      <h1>${t('title')}</h1>
      <p class="sub">${t('subtitle')}</p>
      <p class="tag">${t('tagline')}</p>
    </header>
    <section class="panel">
      <label>${t('difficulty')}</label>
      <div class="segs">${diffBtns}</div>
      <p class="best">${t('best')}: <b>${b ? `${b.correct}/${b.total} · ${fmtTime(b.time)}` : t('none')}</b></p>
      <button class="primary" data-action="play">${t('play')}</button>
      <div class="row">
        <div><label>${t('quality')}</label><div class="segs">${qBtns}</div></div>
        <div><label>${t('language')}</label><div class="segs">${langBtns}</div></div>
      </div>
    </section>
    <section class="panel howto">
      <h2>${t('howto_title')}</h2>
      ${t('howto').map((p) => `<p>${p}</p>`).join('')}
      <h2>${t('controls_title')}</h2>
      <ul class="controls">${controls}</ul>
      <p class="hint-mobile">${t('desktop_hint')}</p>
    </section>
  </div>`;
}

export function introHTML(sequence) {
  const items = sequence.map((id, i) => `
    <li><span class="n">${i + 1}</span><img src="${thumb(id)}" alt=""><span>${esc(itemName(id))}</span></li>`).join('');
  return `
  <div class="modal">
    <h2>${t('intro_title')}</h2>
    <p>${t('intro_text', { n: sequence.length })}</p>
    <ol class="cards">${items}</ol>
    <button class="primary" data-action="start">${t('intro_go')}</button>
  </div>`;
}

export function messageHTML(title, text, action, label) {
  return `
  <div class="modal narrow">
    <h2>${title}</h2>
    <p>${text}</p>
    <button class="primary" data-action="${action}">${label}</button>
  </div>`;
}

export function chooseHTML(locus, candidates, current) {
  const btns = candidates.map((id) => `
    <button class="choice ${id === current ? 'on' : ''}" data-item="${id}">
      <img src="${thumb(id)}" alt=""><span>${esc(itemName(id))}</span>
    </button>`).join('');
  return `
  <div class="modal wide">
    <h2>${t('choose_title', { place: placeName(locus.place) })}</h2>
    <p class="muted">${roomName(locus.room)}</p>
    <div class="choices">${btns}</div>
    <button class="ghost" data-action="cancel">${t('cancel')}</button>
  </div>`;
}

export function resultsHTML({ rows, correct, total, timeMem, timeRec, record }) {
  const ratio = correct / total;
  const rank = t('rank')[ratio === 1 ? 3 : ratio >= 0.7 ? 2 : ratio >= 0.4 ? 1 : 0];
  const stars = ratio === 1 ? 3 : ratio >= 0.7 ? 2 : ratio >= 0.4 ? 1 : 0;
  const body = rows.map((r, i) => `
    <tr class="${r.ok ? 'ok' : 'ko'}">
      <td>${i + 1}</td>
      <td>${esc(placeName(r.locus.place))}<small>${esc(roomName(r.locus.room))}</small></td>
      <td>${r.answer ? `<img src="${thumb(r.answer)}" alt="">${esc(itemName(r.answer))}` : '—'}</td>
      <td><img src="${thumb(r.item)}" alt="">${esc(itemName(r.item))}</td>
      <td class="mark">${r.ok ? '✓' : '✗'}</td>
    </tr>`).join('');
  return `
  <div class="modal wide results">
    <h2>${t('results_title')}</h2>
    <div class="stars">${'★'.repeat(stars)}${'☆'.repeat(3 - stars)}</div>
    <p class="score">${t('results_score', { c: correct, n: total })}</p>
    <p class="rank">${rank}${record ? ` · <b>${t('new_record')}</b>` : ''}</p>
    <p class="muted">${t('time_memorize')}: ${fmtTime(timeMem)} · ${t('time_recall')}: ${fmtTime(timeRec)}</p>
    <div class="table-wrap"><table>
      <thead><tr><th>#</th><th>${t('col_place')}</th><th>${t('col_answer')}</th><th>${t('col_correct')}</th><th></th></tr></thead>
      <tbody>${body}</tbody>
    </table></div>
    <div class="buttons">
      <button class="primary" data-action="again">${t('play_again')}</button>
      <button class="ghost" data-action="review">${t('walk_review')}</button>
      <button class="ghost" data-action="menu">${t('menu')}</button>
    </div>
  </div>`;
}

export function pauseHTML(phase) {
  return `
  <div class="modal narrow">
    <h2>${t('paused')}</h2>
    <div class="buttons column">
      <button class="primary" data-action="resume">${t('resume')}</button>
      ${phase === 'review' ? `<button class="ghost" data-action="results">${t('end_review')}</button>` : `<button class="ghost" data-action="restart">${t('restart')}</button>`}
      <button class="ghost" data-action="menu">${t('menu')}</button>
    </div>
  </div>`;
}

export function listHTML(sequence, placed) {
  return sequence.map((id, i) => `
    <li class="${i < placed ? 'done' : i === placed ? 'current' : ''}">
      <span class="n">${i + 1}</span><img src="${thumb(id)}" alt=""><span>${esc(itemName(id))}</span>
    </li>`).join('');
}
