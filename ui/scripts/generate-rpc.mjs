import { readFileSync } from 'node:fs';
import { serviceBindings, output } from '@gcoms/rpc-codegen';
const contract = JSON.parse(readFileSync(new URL('../schemas/chat-rpc.json', import.meta.url), 'utf8'));
const generated = serviceBindings(contract.service, contract.typescript, 'createChatClient');
output(new URL('../src/rpc-api.ts', import.meta.url), generated.source);
output(new URL('../src/rpc-validators.js', import.meta.url), generated.validators);
