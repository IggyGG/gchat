import { createServer } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('.', import.meta.url));
const server = await createServer({ configFile: false, root, publicDir: fileURLToPath(new URL('../../apps/client/public', import.meta.url)), plugins: [svelte()], server: { host: '127.0.0.1', port: 1428, strictPort: true, fs: { allow: [fileURLToPath(new URL('../..', import.meta.url))] } } });
await server.listen();
