import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { exchangeLocal, exchangeBoundRpc } from '../../ui/server/local';
import { API_VERSION } from '../../ui/src/api';
export default defineConfig({
  plugins: [svelte(), {
    name: 'selected-instance-development-bridge',
    configureServer(server) {
      server.middlewares.use('/_gchat_rpc', async (req, res) => {
        const endpoint = process.env.GCHAT_CHAT_SOCKET;
        const id = process.env.GCHAT_INSTANCE_ID;
        if (!endpoint || !id || req.method !== 'POST' || req.headers.origin !== `http://${req.headers.host}` || !req.headers['content-type']?.startsWith('application/json')) { res.statusCode = 403; res.end('Select one local instance'); return; }
        try {
          let data = ''; for await (const chunk of req) { data += chunk; if (Buffer.byteLength(data) > 32000) throw new Error('request too large'); }
          const reply = await exchangeBoundRpc({ endpoint, id }, JSON.parse(data));
          res.setHeader('Content-Type', 'application/json'); res.setHeader('Cache-Control', 'no-store'); res.end(JSON.stringify(reply));
        } catch { res.statusCode = 502; res.end('Selected instance unavailable'); }
      });
      server.middlewares.use('/_gchat', async (req, res) => {
        // Development only, loopback and same-origin. Production uses native IPC.
        const endpoint = process.env.GCHAT_CHAT_SOCKET;
        const expected = process.env.GCHAT_INSTANCE_ID;
        const origin = req.headers.origin;
        if (!endpoint || !expected || req.method !== 'POST' || origin !== `http://${req.headers.host}` || !req.headers['content-type']?.startsWith('application/json')) { res.statusCode = 403; res.end('Select one local instance in the launch environment'); return; }
        try {
          let data = ''; for await (const chunk of req) { data += chunk; if (Buffer.byteLength(data) > 32000) throw new Error('request too large'); }
          const envelope = JSON.parse(data);
          const blocked = (code: string, message: string) => {
            res.setHeader('Content-Type', 'application/json'); res.setHeader('Cache-Control', 'no-store');
            res.end(JSON.stringify({ version: API_VERSION, instance_id: expected, response: { kind: 'error', code, message } }));
          };
          if (envelope.version !== API_VERSION) { blocked('version', 'Chat API version does not match. Update the client and service together.'); return; }
          if (envelope.request?.kind !== 'identify' && envelope.instance_id !== expected) { blocked('instance', 'Selected instance does not match this attachment. Reopen the selected instance.'); return; }
          const response = await exchangeLocal(endpoint, envelope);
          if (response.instance_id !== expected) { blocked('instance', 'Selected instance changed. Reopen the selected instance.'); return; }
          res.setHeader('Content-Type', 'application/json'); res.setHeader('Cache-Control','no-store'); res.end(JSON.stringify(response));
        } catch { res.statusCode = 502; res.end('Selected instance unavailable'); }
      });
    }
  }],
  clearScreen: false, server: { port: 1420, strictPort: true, watch: { ignored: ["**/src-tauri/**"] } },
  envPrefix: ['VITE_', 'TAURI_ENV_'],
  build: { target: 'es2022' }
});
