// Compresses the raw Blender exports for the web:
//   blender/.cache/models/*.glb  ->  public/models/*.glb
// Textures become WebP, geometry is quantized and meshopt-compressed.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const RAW = 'blender/.cache/models';
const OUT = 'public/models';
const bin = join('node_modules', '.bin', 'gltf-transform');

if (!existsSync(RAW)) {
  console.error(`No raw models in ${RAW}. Run "npm run assets:palace" / "assets:items" first.`);
  process.exit(1);
}

for (const file of readdirSync(RAW).filter((f) => f.endsWith('.glb'))) {
  const src = join(RAW, file);
  const dst = join(OUT, file);
  execFileSync(bin, [
    'optimize', src, dst,
    '--compress', 'meshopt',
    '--texture-compress', 'webp',
    '--texture-size', '1024',
    '--simplify', 'false',
    '--join', 'false',
    '--instance', 'false',
    '--flatten', 'false',
    '--palette', 'false',
  ], { stdio: 'inherit' });
  const mb = (p) => (statSync(p).size / 1e6).toFixed(2);
  console.log(`${file}: ${mb(src)} MB -> ${mb(dst)} MB`);
}

// Item thumbnails rendered by Cycles: PNG -> WebP
const sharp = (await import('sharp')).default;
const THUMBS_RAW = 'blender/.cache/thumbs';
const THUMBS_OUT = 'public/thumbs';
if (existsSync(THUMBS_RAW)) {
  mkdirSync(THUMBS_OUT, { recursive: true });
  const pngs = readdirSync(THUMBS_RAW).filter((f) => f.endsWith('.png'));
  for (const f of pngs) {
    await sharp(join(THUMBS_RAW, f)).resize(192, 192).webp({ quality: 85 }).toFile(join(THUMBS_OUT, f.replace('.png', '.webp')));
  }
  console.log(`thumbnails: ${pngs.length} converted to WebP`);
}
