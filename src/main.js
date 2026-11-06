import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadWorld } from './world.js';
import { Game } from './game.js';
import { detectLang, setLang, t } from './i18n.js';
import { updateMarkerTime } from './markers.js';
import './style.css';

setLang(detectLang());

const canvas = document.getElementById('c');
const loadingEl = document.getElementById('loading');
const barEl = document.getElementById('bar');
document.getElementById('loading-text').textContent = t('loading');

const QUALITY = {
  low: { pixelRatio: 0.75, post: false, ao: false, shadow: 1024 },
  medium: { pixelRatio: 1, post: true, ao: false, shadow: 2048 },
  high: { pixelRatio: 2, post: true, ao: true, shadow: 4096 },
};

function readQuality() {
  try {
    const q = localStorage.getItem('loci.quality');
    if (QUALITY[q]) return q;
  } catch { /* ignore */ }
  return 'medium';
}

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
} catch (err) {
  loadingEl.innerHTML = `<p class="error">${t('webgl_error')}</p>`;
  throw err;
}
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xcfd8e0, 60, 260);
const camera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.05, 3000);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const gtao = new GTAOPass(scene, camera, innerWidth, innerHeight);
gtao.updateGtaoMaterial({ radius: 0.5, distanceExponent: 1.5, thickness: 1.5, scale: 1.0 });
gtao.blendIntensity = 0.85;
composer.addPass(gtao);
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.35, 0.5, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

const settings = {
  quality: readQuality(),
  world: null,
  setQuality(q) {
    this.quality = q;
    try { localStorage.setItem('loci.quality', q); } catch { /* ignore */ }
    applyQuality();
  },
};

function applyQuality() {
  const q = QUALITY[settings.quality];
  renderer.setPixelRatio(Math.min(devicePixelRatio, q.pixelRatio));
  gtao.enabled = q.ao;
  settings.world?.setShadowQuality(q.shadow);
  resize();
}

function resize() {
  const w = innerWidth;
  const h = innerHeight;
  renderer.setSize(w, h);
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);

async function start() {
  const world = await loadWorld(renderer, scene, (p) => {
    barEl.style.width = `${Math.round(p * 100)}%`;
  });
  settings.world = world;
  applyQuality();
  const game = new Game({ scene, camera, canvas, world, settings });
  // compile shaders up front to avoid hitches when walking into rooms
  renderer.compile(scene, camera);
  loadingEl.classList.add('done');
  setTimeout(() => loadingEl.remove(), 800);

  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.05);
    const time = clock.elapsedTime;
    game.update(dt, time);
    updateMarkerTime(time);
    if (QUALITY[settings.quality].post) composer.render(dt);
    else renderer.render(scene, camera);
  });
  window.__loci = { game, renderer, scene, camera };
}

start().catch((err) => {
  console.error(err);
  loadingEl.innerHTML = `<p class="error">${err.message}</p>`;
});
