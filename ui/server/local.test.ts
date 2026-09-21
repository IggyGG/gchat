import { afterEach, describe, expect, it } from 'vitest';
import { createServer, type Server } from 'node:net';
import { chmod, mkdtemp, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { exchangeLocal } from './local';

const resources: { directory: string; server: Server }[] = [];
const request = { version: 1, instance_id: null, request: { kind: 'identify' as const } };
async function endpoint(reply: Buffer) {
  const directory = await mkdtemp(join(tmpdir(), 'gchat-bridge-'));
  await chmod(directory, 0o700);
  const path = join(directory, 'chat.sock');
  const server = createServer(socket => {
    socket.once('data', () => socket.end(reply));
    socket.on('error', () => {});
  });
  resources.push({ directory, server });
  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(path, () => {
      server.removeListener('error', reject);
      resolve();
    });
  });
  await chmod(path, 0o600);
  return { directory, path };
}
afterEach(async () => {
  for (const { directory, server } of resources.splice(0)) {
    await new Promise<void>(resolve => server.close(() => resolve()));
    await rm(directory, { recursive: true, force: true });
  }
});
it('refuses the browser bridge without Unix peer ownership support', async () => {
  const descriptor = Object.getOwnPropertyDescriptor(process, 'getuid');
  try {
    Object.defineProperty(process, 'getuid', { configurable: true, value: undefined });
    await expect(exchangeLocal(join(tmpdir(), 'nonexistent-gchat-bridge', 'chat.sock'), request))
      .rejects.toThrow('This browser bridge requires Unix private sockets');
  } finally {
    if (descriptor) Object.defineProperty(process, 'getuid', descriptor);
    else Reflect.deleteProperty(process, 'getuid');
  }
});

// The optional Node browser bridge authenticates Unix sockets. Windows desktop
// clients use gchat-api's separately tested native named-pipe transport.
describe.skipIf(typeof process.getuid !== 'function')('selected private Unix service bridge', () => {
  it('decodes a framed response without changing its payload', async () => {
    const response = { version: 1, instance_id: 'selected', response: { kind: 'applied', conversation: null, notice: '  λ  ' } };
    const body = Buffer.from(JSON.stringify(response));
    const header = Buffer.alloc(4); header.writeUInt32BE(body.length);
    const { path } = await endpoint(Buffer.concat([header, body]));
    await expect(exchangeLocal(path, request)).resolves.toEqual(response);
  });
  it('refuses an oversized declared response before allocating its body', async () => {
    const header = Buffer.alloc(4); header.writeUInt32BE(16 * 1024 * 1024 + 1);
    const { path } = await endpoint(header);
    await expect(exchangeLocal(path, request)).rejects.toThrow('Invalid chat frame');
  });
  it('refuses shared directories and socket symlinks', async () => {
    const { path, directory } = await endpoint(Buffer.alloc(0));
    await chmod(directory, 0o755);
    await expect(exchangeLocal(path, request)).rejects.toThrow('owner-only');
    await chmod(directory, 0o700);
    const alias = join(directory, 'alias');
    await symlink(path, alias);
    await expect(exchangeLocal(alias, request)).rejects.toThrow('owner-only');
  });
});
