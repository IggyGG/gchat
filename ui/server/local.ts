// Server-only bridge. Endpoint comes from trusted launch configuration, never HTTP input.
import { connect } from 'node:net';
import { lstat } from 'node:fs/promises';
import { dirname } from 'node:path';
import type { RequestEnvelope, ResponseEnvelope } from '../src/api';
import { isRequest, isReply, type Request as RpcRequest, type Reply } from '@gcoms/rpc';
const MAX = 16 * 1024 * 1024;
export async function exchangeLocal(endpoint: string, request: RequestEnvelope): Promise<ResponseEnvelope> {
  return exchangeFrame(endpoint, request) as Promise<ResponseEnvelope>;
}

export async function exchangeLocalRpc(endpoint: string, request: RpcRequest): Promise<Reply> {
  if (!isRequest(request)) throw new Error('Invalid RPC request');
  const reply = await exchangeFrame(endpoint + '.rpc', request);
  if (!isReply(reply) || reply.rpc !== 1 || reply.id !== request.id || reply.instance !== request.instance || reply.service !== request.service || reply.version !== request.version || reply.method !== request.method) throw new Error('Invalid RPC response binding');
  return reply;
}

/** An authenticated gateway may forward only its configured chat instance. */
export async function exchangeBoundRpc(binding: { endpoint: string; id: string }, value: unknown): Promise<Reply> {
  if (!isRequest(value) || value.rpc !== 1 || value.instance !== binding.id || value.service !== 'ghost.chat' || value.version !== 1) throw new Error('Selected instance or service version mismatch');
  return exchangeLocalRpc(binding.endpoint, value);
}

async function exchangeFrame(endpoint: string, request: unknown): Promise<unknown> {
  // Browser bridges currently run on Unix. Native clients use gchat-api,
  // including its Windows named-pipe peer ownership checks.
  if (!process.getuid) throw new Error('This browser bridge requires Unix private sockets');
  const [socketFile, parent] = await Promise.all([lstat(endpoint), lstat(dirname(endpoint))]);
  const uid = process.getuid();
  if (!socketFile.isSocket() || !parent.isDirectory() || socketFile.uid !== uid || parent.uid !== uid || (socketFile.mode & 0o077) || (parent.mode & 0o077)) throw new Error('Selected chat endpoint is not owner-only');
  return new Promise((resolve, reject) => {
    const body = Buffer.from(JSON.stringify(request));
    if (body.length > MAX) { reject(new Error('Chat request exceeds bound')); return; }
    const socket = connect(endpoint);
    let data = Buffer.alloc(0);
    let expected: number | undefined;
    let settled = false;
    const fail = (error: Error) => { if (!settled) { settled = true; reject(error); } socket.destroy(); };
    socket.setTimeout(150_000, () => fail(new Error('Selected instance timed out')));
    socket.on('error', fail);
    socket.on('end', () => { if (!settled) fail(new Error('Selected instance closed an incomplete response')); });
    socket.on('connect', () => { const header = Buffer.alloc(4); header.writeUInt32BE(body.length); socket.write(header); socket.write(body); });
    socket.on('data', chunk => {
      if (data.length + chunk.length > MAX + 4) { fail(new Error('Chat response exceeds bound')); return; }
      data = Buffer.concat([data, chunk]);
      if (expected === undefined && data.length >= 4) {
        expected = data.readUInt32BE(0);
        if (expected > MAX || expected === 0) { fail(new Error('Invalid chat frame')); return; }
      }
      if (expected !== undefined && data.length >= expected + 4) {
        try { const value = JSON.parse(data.subarray(4, expected + 4).toString('utf8')); settled = true; resolve(value); socket.destroy(); }
        catch { fail(new Error('Invalid chat response')); }
      }
    });
  });
}
