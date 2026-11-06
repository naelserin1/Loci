// Visual helpers: golden light beam, glowing rings and numbered labels.
import * as THREE from 'three';

const beamMat = new THREE.ShaderMaterial({
  uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(1.0, 0.78, 0.35) } },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
  fragmentShader: /* glsl */ `
    uniform float uTime;
    uniform vec3 uColor;
    varying vec2 vUv;
    void main() {
      float fade = pow(1.0 - vUv.y, 1.6);
      float stripes = 0.75 + 0.25 * sin(vUv.y * 30.0 - uTime * 3.0);
      float edge = pow(abs(sin(vUv.x * 3.14159 * 2.0)), 0.5);
      gl_FragColor = vec4(uColor * 3.0, fade * stripes * (0.45 + 0.45 * edge));
    }`,
  transparent: true,
  depthWrite: false,
  blending: THREE.AdditiveBlending,
  side: THREE.DoubleSide,
});

const ringMat = new THREE.ShaderMaterial({
  uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(1.0, 0.8, 0.4) }, uAlpha: { value: 1 } },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
  fragmentShader: /* glsl */ `
    uniform float uTime;
    uniform vec3 uColor;
    uniform float uAlpha;
    varying vec2 vUv;
    void main() {
      float r = length(vUv - 0.5) * 2.0;
      float ring = smoothstep(0.62, 0.72, r) * (1.0 - smoothstep(0.8, 0.98, r));
      float pulse = 0.65 + 0.35 * sin(uTime * 3.0);
      gl_FragColor = vec4(uColor * 2.0, ring * pulse * uAlpha);
    }`,
  transparent: true,
  depthWrite: false,
  blending: THREE.AdditiveBlending,
});

export function updateMarkerTime(t) {
  beamMat.uniforms.uTime.value = t;
  ringMat.uniforms.uTime.value = t;
}

export function createBeam() {
  const g = new THREE.CylinderGeometry(0.32, 0.42, 3.2, 32, 1, true);
  g.translate(0, 1.6, 0);
  const m = new THREE.Mesh(g, beamMat);
  m.renderOrder = 10;
  m.frustumCulled = false;
  return m;
}

export function createRing(color) {
  const mat = ringMat.clone();
  mat.uniforms = THREE.UniformsUtils.clone(ringMat.uniforms);
  mat.uniforms.uTime = ringMat.uniforms.uTime; // shared clock
  if (color) mat.uniforms.uColor.value.set(color);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 1.1), mat);
  m.rotation.x = -Math.PI / 2;
  m.renderOrder = 9;
  return m;
}

export function createLabel(text, color = '#f3d58a') {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(20,16,12,0.72)';
  g.beginPath();
  g.arc(64, 64, 56, 0, Math.PI * 2);
  g.fill();
  g.strokeStyle = color;
  g.lineWidth = 6;
  g.stroke();
  g.fillStyle = color;
  g.font = 'bold 64px Georgia, serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(text, 64, 68);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthWrite: false, transparent: true }));
  s.scale.setScalar(0.28);
  s.renderOrder = 11;
  return s;
}
