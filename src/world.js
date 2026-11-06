// Loads the Blender-built palace and items and sets up lighting.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const BASE = import.meta.env.BASE_URL;
const LIGHT_SCALE = 1.0;

export async function loadWorld(renderer, scene, onProgress) {
  const manager = new THREE.LoadingManager();
  manager.onProgress = (_url, loaded, total) => onProgress?.(loaded / total);
  const loader = new GLTFLoader(manager);
  loader.setMeshoptDecoder(MeshoptDecoder);

  const [palaceGltf, itemsGltf, data] = await Promise.all([
    loader.loadAsync(`${BASE}models/palace.glb`),
    loader.loadAsync(`${BASE}models/items.glb`),
    fetch(`${BASE}models/palace.json`).then((r) => r.json()),
  ]);

  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  const palace = palaceGltf.scene;
  palace.traverse((o) => {
    if (!o.isMesh) return;
    const name = o.material.name || '';
    const noShadow = /glass|flame|ember|water|ground/.test(name);
    o.castShadow = !noShadow;
    o.receiveShadow = !/flame|ember/.test(name);
    for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap']) {
      if (o.material[key]) o.material[key].anisotropy = maxAniso;
    }
    if (name === 'glass') {
      o.material.transparent = true;
      o.material.depthWrite = false;
      o.material.envMapIntensity = 1.5;
    }
    if (name === 'water') o.material.envMapIntensity = 1.4;
  });
  scene.add(palace);

  // Item templates, normalized so every object reads at a similar size.
  const items = new Map();
  const box = new THREE.Box3();
  const size = new THREE.Vector3();
  for (const node of [...itemsGltf.scene.children]) {
    if (!node.name.startsWith('item_')) continue;
    const id = node.name.slice(5);
    const pivot = new THREE.Group();
    node.position.set(0, 0, 0);
    pivot.add(node);
    box.setFromObject(node);
    box.getSize(size);
    const s = 0.4 / Math.max(size.x, size.y, size.z);
    node.scale.setScalar(s);
    box.setFromObject(node);
    const c = box.getCenter(new THREE.Vector3());
    node.position.set(-c.x, -box.min.y, -c.z);
    node.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = !/glass|flame/.test(o.material.name);
        if (/glass/.test(o.material.name)) {
          o.material.transparent = true;
          o.material.depthWrite = false;
        }
      }
    });
    items.set(id, pivot);
  }

  // Sky + sun
  const sky = new Sky();
  sky.scale.setScalar(4000);
  const sunDir = new THREE.Vector3(...data.sun.dir).normalize();
  const u = sky.material.uniforms;
  u.turbidity.value = 4;
  u.rayleigh.value = 1.4;
  u.mieCoefficient.value = 0.004;
  u.mieDirectionalG.value = 0.85;
  u.sunPosition.value.copy(sunDir).multiplyScalar(1000);
  scene.add(sky);

  const sun = new THREE.DirectionalLight(0xfff0d8, 3.2);
  const center = new THREE.Vector3(6, 0, -19);
  sun.position.copy(center).addScaledVector(sunDir, 60);
  sun.target.position.copy(center);
  sun.castShadow = true;
  const sc = sun.shadow.camera;
  sc.left = -26; sc.right = 26; sc.top = 26; sc.bottom = -26; sc.near = 10; sc.far = 130;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);

  const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x6b5a45, 0.25);
  scene.add(hemi);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.18;

  // Candle-lit point lights
  const lights = [];
  for (const l of data.lights) {
    const p = new THREE.PointLight(l.color, l.intensity * LIGHT_SCALE, l.distance * 1.4, 2);
    p.position.set(...l.pos);
    p.userData = { base: l.intensity * LIGHT_SCALE, flicker: l.flicker, seed: Math.random() * 100 };
    scene.add(p);
    lights.push(p);
  }

  // Ambient level depends on whether the player is indoors or in the courtyard.
  let outdoor = 0;
  function update(time, dt, isOutdoor) {
    outdoor += ((isOutdoor ? 1 : 0) - outdoor) * Math.min(1, dt * 2);
    scene.environmentIntensity = 0.18 + 0.35 * outdoor;
    hemi.intensity = 0.25 + 0.6 * outdoor;
    for (const p of lights) {
      if (!p.userData.flicker) continue;
      const s = p.userData.seed;
      const f = 0.86 + 0.08 * Math.sin(time * 7.1 + s) + 0.06 * Math.sin(time * 13.7 + s * 2.3);
      p.intensity = p.userData.base * f;
    }
  }

  function setShadowQuality(size) {
    sun.shadow.mapSize.set(size, size);
    if (sun.shadow.map) {
      sun.shadow.map.dispose();
      sun.shadow.map = null;
    }
  }

  return { palace, items, data, sun, lights, update, setShadowQuality };
}
