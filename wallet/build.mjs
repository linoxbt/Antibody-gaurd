// Bundle wallet.ts for the browser. REOWN_PROJECT_ID (optional) is baked in at build time.
import { build } from 'esbuild';
import { mkdirSync, writeFileSync } from 'node:fs';

const id = process.env.REOWN_PROJECT_ID ?? '';
if (id && !/^[0-9a-f]{32}$/i.test(id)) throw new Error('REOWN_PROJECT_ID must be 32 hex characters');
mkdirSync('dist', { recursive: true });
const r = await build({
  entryPoints: ['wallet.ts'], bundle: true, splitting: true, format: 'esm', minify: true, target: 'es2022',
  outdir: 'dist', entryNames: 'wallet', chunkNames: 'w-[hash]', legalComments: 'none', metafile: true,
  define: { 'process.env.NODE_ENV': '"production"', 'process.env.REOWN_PROJECT_ID': JSON.stringify(id), global: 'globalThis' },
});
writeFileSync('dist/meta.json', JSON.stringify(r.metafile));
