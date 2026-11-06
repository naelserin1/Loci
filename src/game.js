// Game flow: menu -> memorize -> recall -> results (-> review).
import * as THREE from 'three';
import { Player } from './player.js';
import { createBeam, createLabel, createRing } from './markers.js';
import {
  t, setLang, getLang, roomName, placeName, itemWithArticle, itemImage, ITEM_IDS,
} from './i18n.js';
import {
  DIFFICULTIES, menuHTML, introHTML, messageHTML, chooseHTML, resultsHTML, pauseHTML, listHTML, fmtTime,
} from './ui.js';

const $ = (id) => document.getElementById(id);

function shuffle(a, rnd = Math.random) {
  const r = a.slice();
  for (let i = r.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [r[i], r[j]] = [r[j], r[i]];
  }
  return r;
}

function load(key, fallback) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch {
    return fallback;
  }
}

function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ }
}

export class Game {
  constructor({ scene, camera, canvas, world, settings }) {
    this.scene = scene;
    this.camera = camera;
    this.canvas = canvas;
    this.world = world;
    this.settings = settings;
    this.data = world.data;
    this.player = new Player(camera, canvas, this.data.colliders);
    this.overlay = $('overlay');
    this.hud = $('hud');
    this.phase = 'menu';
    this.paused = false;
    this.difficulty = load('loci.difficulty', 'normal');
    this.best = load('loci.best', {});
    this.placed = new Map(); // locus id -> object
    this.markers = new THREE.Group();
    scene.add(this.markers);
    this.beam = createBeam();
    this.beam.visible = false;
    scene.add(this.beam);
    this.room = null;
    this.focus = null;
    this.clock = 0;

    this.overlay.addEventListener('click', (e) => this.onOverlayClick(e));
    window.addEventListener('keydown', (e) => this.onKey(e));
    canvas.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      if (this.player.locked) this.interact();
      else if (this.isActive() && !this.overlayOpen()) this.player.lock();
    });
    document.addEventListener('pointerlockchange', () => this.onLockChange());
    document.addEventListener('pointerlockerror', () => {
      if (this.isActive()) this.showOverlay(`<div class="modal narrow click"><p>${t('click_to_play')}</p>
        <button class="primary" data-action="resume">${t('resume')}</button></div>`);
    });

    // Idle camera for the menu: slow drift through the vestibule.
    this.player.teleport(this.data.spawn.pos, this.data.spawn.yaw);
    this.showMenu();
  }

  // ------------------------------------------------------------------ state

  isActive() {
    return ['memorize', 'recall', 'review'].includes(this.phase);
  }

  overlayOpen() {
    return !this.overlay.hidden;
  }

  showOverlay(html) {
    this.overlay.innerHTML = html;
    this.overlay.hidden = false;
    this.player.enabled = false;
  }

  hideOverlay() {
    this.overlay.hidden = true;
    this.overlay.innerHTML = '';
  }

  enterPlay() {
    this.hideOverlay();
    this.paused = false;
    this.player.enabled = true;
    this.player.lock();
  }

  showMenu() {
    this.phase = 'menu';
    this.hud.hidden = true;
    this.clearLoci();
    this.player.unlock();
    this.showOverlay(menuHTML({ difficulty: this.difficulty, quality: this.settings.quality, best: this.best }));
    this.overlay.classList.add('menu-bg');
  }

  newGame() {
    this.overlay.classList.remove('menu-bg');
    const cfg = DIFFICULTIES[this.difficulty];
    this.loci = cfg.loci.map((id) => this.data.loci.find((l) => l.id === id));
    this.sequence = shuffle(ITEM_IDS).slice(0, cfg.count);
    const others = shuffle(ITEM_IDS.filter((id) => !this.sequence.includes(id)));
    this.candidates = shuffle([...this.sequence, ...others.slice(0, cfg.options - cfg.count)]);
    this.answers = new Map();
    this.placedCount = 0;
    this.timeMem = 0;
    this.timeRec = 0;
    this.clearLoci();
    this.player.teleport(this.data.spawn.pos, this.data.spawn.yaw);
    this.phase = 'intro';
    this.hud.hidden = true;
    this.showOverlay(introHTML(this.sequence));
  }

  startMemorize() {
    this.phase = 'memorize';
    this.hud.hidden = false;
    this.buildLabels();
    this.updateHUD();
    this.enterPlay();
  }

  allPlaced() {
    return this.placedCount >= this.loci.length;
  }

  startRecallIntro() {
    this.phase = 'recall_intro';
    this.player.unlock();
    this.showOverlay(messageHTML(t('recall_intro_title'), t('recall_intro_text'), 'recall', t('recall_go')));
  }

  startRecall() {
    for (const obj of this.placed.values()) this.scene.remove(obj);
    this.placed.clear();
    this.player.teleport(this.data.spawn.pos, this.data.spawn.yaw);
    this.phase = 'recall';
    this.beam.visible = false;
    this.buildLabels();
    this.updateHUD();
    this.enterPlay();
  }

  finish() {
    const rows = this.loci.map((locus, i) => {
      const answer = this.answers.get(locus.id);
      const item = this.sequence[i];
      return { locus, answer, item, ok: answer === item };
    });
    const correct = rows.filter((r) => r.ok).length;
    const total = rows.length;
    const prev = this.best[this.difficulty];
    const totalTime = this.timeMem + this.timeRec;
    const record = !prev || correct > prev.correct || (correct === prev.correct && totalTime < prev.time);
    if (record) {
      this.best[this.difficulty] = { correct, total, time: totalTime };
      save('loci.best', this.best);
    }
    this.lastResults = { rows, correct, total, timeMem: this.timeMem, timeRec: this.timeRec, record };
    this.showResults();
  }

  showResults() {
    this.phase = 'results';
    this.hud.hidden = true;
    this.beam.visible = false;
    this.player.unlock();
    this.showOverlay(resultsHTML(this.lastResults));
  }

  startReview() {
    this.phase = 'review';
    for (const obj of this.placed.values()) this.scene.remove(obj);
    this.placed.clear();
    this.clearMarkers();
    this.lastResults.rows.forEach((r) => {
      this.placeItem(r.locus, r.item, false);
      const ring = createRing(r.ok ? '#7dff9a' : '#ff6b6b');
      ring.position.set(r.locus.pos[0], r.locus.pos[1] + 0.012, r.locus.pos[2]);
      this.markers.add(ring);
    });
    this.hud.hidden = false;
    this.updateHUD();
    this.enterPlay();
  }

  // ------------------------------------------------------------------ loci

  clearMarkers() {
    for (const m of [...this.markers.children]) {
      this.markers.remove(m);
      m.material.map?.dispose();
      m.material.dispose();
      m.geometry?.dispose();
    }
  }

  clearLoci() {
    for (const obj of this.placed.values()) this.scene.remove(obj);
    this.placed.clear();
    this.clearMarkers();
    this.beam.visible = false;
  }

  buildLabels() {
    this.clearMarkers();
    this.loci.forEach((locus, i) => {
      const label = createLabel(String(i + 1));
      label.position.set(locus.pos[0], locus.pos[1] + 0.78, locus.pos[2]);
      label.userData.locus = locus.id;
      this.markers.add(label);
      if (this.phase === 'recall') {
        const ring = createRing();
        ring.position.set(locus.pos[0], locus.pos[1] + 0.012, locus.pos[2]);
        ring.userData.locus = locus.id;
        this.markers.add(ring);
      }
    });
  }

  placeItem(locus, itemId, animate = true) {
    const old = this.placed.get(locus.id);
    if (old) this.scene.remove(old);
    const obj = this.world.items.get(itemId).clone();
    obj.position.set(locus.pos[0], locus.pos[1] + 0.02, locus.pos[2]);
    obj.userData = { spawn: animate ? 0 : 1, baseY: locus.pos[1] + 0.02, phase: Math.random() * 6 };
    obj.scale.setScalar(animate ? 0.001 : 1);
    this.scene.add(obj);
    this.placed.set(locus.id, obj);
  }

  findFocus() {
    if (!this.loci) return null;
    const camPos = this.camera.position;
    const fwd = this.player.forward(new THREE.Vector3());
    const v = new THREE.Vector3();
    let best = null;
    let bestScore = Infinity;
    const candidates = this.phase === 'memorize'
      ? (this.allPlaced() ? [] : [this.loci[this.placedCount]])
      : this.phase === 'recall' ? this.loci : [];
    for (const locus of candidates) {
      v.set(locus.pos[0], locus.pos[1] + 0.2, locus.pos[2]).sub(camPos);
      const dist = v.length();
      if (dist > 3.2) continue;
      const along = v.dot(fwd);
      if (along <= 0) continue;
      const off = Math.sqrt(Math.max(0, dist * dist - along * along));
      if (off > (locus.radius ?? 0.6) + 0.25) continue;
      if (dist < bestScore) {
        best = locus;
        bestScore = dist;
      }
    }
    return best;
  }

  interact() {
    const locus = this.focus;
    if (!locus) return;
    if (this.phase === 'memorize') {
      const item = this.sequence[this.placedCount];
      this.placeItem(locus, item);
      this.showVivid(itemImage(item, placeName(locus.place)));
      this.placedCount++;
      if (this.allPlaced()) {
        this.showVivid(t('all_placed_text'), 9000, t('all_placed_title'));
      }
      this.updateHUD();
    } else if (this.phase === 'recall') {
      this.choosing = locus;
      this.player.unlock();
      this.showOverlay(chooseHTML(locus, this.candidates, this.answers.get(locus.id)));
    }
  }

  choose(itemId) {
    const locus = this.choosing;
    this.choosing = null;
    if (locus && itemId) {
      this.answers.set(locus.id, itemId);
      this.placeItem(locus, itemId);
    }
    this.updateHUD();
    this.enterPlay();
  }

  // ------------------------------------------------------------------ HUD

  showVivid(html, ms = 6500, label = t('imagine')) {
    const el = $('vivid');
    el.innerHTML = `${label ? `<span class="label">${label}</span>` : ''}${html}`;
    el.classList.add('show');
    clearTimeout(this.vividTimer);
    this.vividTimer = setTimeout(() => el.classList.remove('show'), ms);
  }

  showRoomToast(room) {
    const el = $('room-toast');
    el.textContent = roomName(room);
    el.classList.remove('show');
    void el.offsetWidth;
    el.classList.add('show');
  }

  updateHUD() {
    const phaseName = { memorize: 'phase_memorize', recall: 'phase_recall', review: 'phase_review' }[this.phase];
    $('phase').textContent = phaseName ? t(phaseName) : '';
    const list = $('list');
    if (this.phase === 'memorize') {
      list.hidden = false;
      list.innerHTML = listHTML(this.sequence, this.placedCount);
      list.classList.toggle('compact', this.sequence.length > 8);
      list.querySelector('.current')?.scrollIntoView({ block: 'nearest' });
      $('progress').textContent = `${this.placedCount}/${this.loci.length}`;
    } else {
      list.hidden = true;
      $('progress').textContent = this.phase === 'recall'
        ? `${t('answered')}: ${this.answers.size}/${this.loci.length}` : '';
    }
  }

  updatePrompt() {
    const el = $('prompt');
    const hint = $('hint');
    let text = '';
    let hintText = '';
    if (this.phase === 'memorize') {
      if (this.focus) {
        text = t('place_prompt', { item: itemWithArticle(this.sequence[this.placedCount]), place: placeName(this.focus.place) });
      } else if (this.allPlaced()) {
        hintText = t('ready_prompt');
      } else {
        hintText = t('follow_light');
      }
    } else if (this.phase === 'recall') {
      if (this.focus) {
        const key = this.answers.has(this.focus.id) ? 'recall_change' : 'recall_prompt';
        text = t(key, { place: placeName(this.focus.place) });
      }
      if (this.answers.size === this.loci.length) hintText = t('finish_prompt');
    }
    el.innerHTML = text ? `<kbd>E</kbd> ${text}` : '';
    el.classList.toggle('show', !!text);
    hint.textContent = hintText;
    $('crosshair').classList.toggle('active', !!this.focus);
  }

  // ------------------------------------------------------------------ input

  onOverlayClick(e) {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.dataset.diff) {
      this.difficulty = btn.dataset.diff;
      save('loci.difficulty', this.difficulty);
      this.showMenu();
      return;
    }
    if (btn.dataset.quality) {
      this.settings.setQuality(btn.dataset.quality);
      this.showMenu();
      return;
    }
    if (btn.dataset.lang) {
      setLang(btn.dataset.lang);
      this.showMenu();
      return;
    }
    if (btn.dataset.item) {
      this.choose(btn.dataset.item);
      return;
    }
    switch (btn.dataset.action) {
      case 'play':
      case 'again':
        this.newGame();
        break;
      case 'start':
        this.startMemorize();
        break;
      case 'recall':
        this.startRecall();
        break;
      case 'cancel':
        this.choose(null);
        break;
      case 'resume':
        this.enterPlay();
        break;
      case 'restart':
        this.newGame();
        break;
      case 'review':
        this.startReview();
        break;
      case 'results':
        this.clearLoci();
        this.showResults();
        break;
      case 'menu':
        this.showMenu();
        break;
      default:
    }
  }

  onKey(e) {
    if (e.repeat) return;
    if (this.choosing && e.code === 'Escape') {
      this.choose(null);
      return;
    }
    if (!this.player.locked) return;
    if (e.code === 'KeyE') this.interact();
    if (e.code === 'KeyR' && this.phase === 'memorize' && this.allPlaced()) this.startRecallIntro();
    if (e.code === 'KeyF' && this.phase === 'recall' && this.answers.size === this.loci.length) this.finish();
  }

  onLockChange() {
    if (this.player.locked) {
      this.player.enabled = true;
      return;
    }
    this.player.enabled = false;
    if (this.isActive() && !this.choosing && !this.overlayOpen()) {
      this.paused = true;
      this.showOverlay(pauseHTML(this.phase));
    }
  }

  // ------------------------------------------------------------------ loop

  update(dt, time) {
    this.clock = time;
    const playing = this.isActive() && !this.overlayOpen();
    if (playing) {
      this.player.update(dt);
      if (this.phase === 'memorize') this.timeMem += dt;
      if (this.phase === 'recall') this.timeRec += dt;
      $('timer').textContent = fmtTime(this.phase === 'recall' ? this.timeRec : this.timeMem);
    } else if (this.phase === 'menu') {
      // gentle idle camera
      const a = time * 0.06;
      this.camera.position.set(Math.sin(a) * 1.2, 1.7, -1.4 - Math.sin(a * 0.5) * 0.6);
      this.camera.rotation.set(0.12, Math.sin(a * 0.7) * 0.45 - 0.25, 0, 'YXZ');
    }

    // room detection
    const p = this.camera.position;
    const room = this.data.rooms.find((r) => p.x >= r.min[0] && p.x <= r.max[0] && p.z >= r.min[1] && p.z <= r.max[1]);
    if (room && room.id !== this.room) {
      this.room = room.id;
      if (playing) this.showRoomToast(room.id);
    }
    this.world.update(time, dt, room?.outdoor);

    // beam over the next locus
    if (this.phase === 'memorize' && !this.allPlaced()) {
      const l = this.loci[this.placedCount];
      this.beam.position.set(l.pos[0], l.pos[1], l.pos[2]);
      this.beam.visible = true;
    } else {
      this.beam.visible = false;
    }

    // labels: show the next one in memorize, unanswered ones in recall
    for (const m of this.markers.children) {
      const id = m.userData.locus;
      if (id === undefined) continue;
      if (this.phase === 'memorize') {
        m.visible = m.isSprite && this.loci[this.placedCount]?.id === id;
      } else if (this.phase === 'recall') {
        m.visible = m.isSprite ? true : !this.answers.has(id);
      }
    }

    // animate placed objects
    for (const obj of this.placed.values()) {
      const u = obj.userData;
      if (u.spawn < 1) {
        u.spawn = Math.min(1, u.spawn + dt * 2.5);
        const k = u.spawn;
        obj.scale.setScalar(1 + 0.25 * Math.sin(k * Math.PI) - (1 - k) * (1 - k));
      }
      obj.rotation.y += dt * 0.5;
      obj.position.y = u.baseY + 0.03 + Math.sin(time * 1.6 + u.phase) * 0.02;
    }

    this.focus = playing ? this.findFocus() : null;
    if (this.isActive()) this.updatePrompt();
  }

  refreshTexts() {
    if (this.phase === 'menu') this.showMenu();
  }

  get lang() {
    return getLang();
  }
}
