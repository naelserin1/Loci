// First-person walker with pointer-lock mouse look and 2D collision.
import * as THREE from 'three';

const EYE = 1.65;
const RADIUS = 0.3;
const WALK = 3.0;
const RUN = 5.4;

export class Player {
  constructor(camera, dom, colliders) {
    this.camera = camera;
    this.dom = dom;
    this.colliders = colliders;
    this.pos = new THREE.Vector3();
    this.vel = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = 0;
    this.keys = new Set();
    this.enabled = false;
    this.bob = 0;
    this.sensitivity = 0.0022;

    document.addEventListener('mousemove', (e) => {
      if (!this.enabled || !this.locked) return;
      // some browsers report a huge jump right after locking the pointer
      if (Math.abs(e.movementX) > 250 || Math.abs(e.movementY) > 250) return;
      this.yaw -= e.movementX * this.sensitivity;
      this.pitch -= e.movementY * this.sensitivity;
      this.pitch = Math.max(-1.45, Math.min(1.45, this.pitch));
    });
    window.addEventListener('keydown', (e) => this.keys.add(e.code));
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());
  }

  get locked() {
    return document.pointerLockElement === this.dom;
  }

  lock() {
    const p = this.dom.requestPointerLock?.();
    if (p && p.catch) p.catch(() => {});
  }

  unlock() {
    if (this.locked) document.exitPointerLock();
  }

  teleport(pos, yaw = 0) {
    this.pos.set(pos[0], 0, pos[2]);
    this.vel.set(0, 0, 0);
    this.yaw = yaw;
    this.pitch = 0;
    this.applyCamera(0);
  }

  update(dt) {
    const k = this.keys;
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    const run = k.has('ShiftLeft') || k.has('ShiftRight');
    const target = new THREE.Vector3();
    if (this.enabled && (f || s)) {
      const sin = Math.sin(this.yaw);
      const cos = Math.cos(this.yaw);
      target.set(-sin * f + cos * s, 0, -cos * f - sin * s).normalize().multiplyScalar(run ? RUN : WALK);
    }
    const accel = target.lengthSq() > 0 ? 10 : 12;
    this.vel.lerp(target, 1 - Math.exp(-accel * dt));
    this.pos.addScaledVector(this.vel, dt);
    this.collide();
    const speed = Math.hypot(this.vel.x, this.vel.z);
    this.bob += dt * speed * 2.2;
    this.applyCamera(speed);
  }

  applyCamera(speed) {
    const amp = Math.min(speed / RUN, 1) * 0.035;
    this.camera.position.set(this.pos.x, EYE + Math.sin(this.bob * 2) * amp, this.pos.z);
    this.camera.rotation.set(this.pitch, this.yaw, Math.sin(this.bob) * amp * 0.15, 'YXZ');
  }

  collide() {
    const p = this.pos;
    for (let iter = 0; iter < 3; iter++) {
      for (const c of this.colliders) {
        if (c.type === 'rect') {
          const cx = Math.max(c.min[0], Math.min(p.x, c.max[0]));
          const cz = Math.max(c.min[1], Math.min(p.z, c.max[1]));
          let dx = p.x - cx;
          let dz = p.z - cz;
          const d2 = dx * dx + dz * dz;
          if (d2 > RADIUS * RADIUS) continue;
          if (d2 > 1e-10) {
            const d = Math.sqrt(d2);
            p.x += (dx / d) * (RADIUS - d);
            p.z += (dz / d) * (RADIUS - d);
          } else {
            // centre inside the box: push out along the shallowest axis
            const pen = [p.x - c.min[0], c.max[0] - p.x, p.z - c.min[1], c.max[1] - p.z];
            const i = pen.indexOf(Math.min(...pen));
            if (i === 0) p.x = c.min[0] - RADIUS;
            else if (i === 1) p.x = c.max[0] + RADIUS;
            else if (i === 2) p.z = c.min[1] - RADIUS;
            else p.z = c.max[1] + RADIUS;
          }
        } else {
          const dx = p.x - c.c[0];
          const dz = p.z - c.c[1];
          const min = c.r + RADIUS;
          const d2 = dx * dx + dz * dz;
          if (d2 >= min * min) continue;
          const d = Math.sqrt(d2) || 1e-5;
          p.x = c.c[0] + (dx / d) * min;
          p.z = c.c[1] + (dz / d) * min;
        }
      }
    }
  }

  forward(out = new THREE.Vector3()) {
    return this.camera.getWorldDirection(out);
  }
}
