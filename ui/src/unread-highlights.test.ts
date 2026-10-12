import { describe, expect, it } from 'vitest';
import { callsAttention, UnreadHighlights } from './unread-highlights';
import type { Conversation, Message, Response, Snapshot } from './api';

const conversation = { id:'a', unread:2, lastMessageId:'tail', members:[{ nickname:'Iggy', isSelf:true }] } as Conversation;
const message = (body:string, extra:Partial<Message> = {}) => ({ body, mine:false, ...extra } as Message);
const snapshot = (conversations = [conversation], id = 'profile') => ({ instance:{ id, bootId:'boot', locked:false }, conversations } as Snapshot);
const flush = () => new Promise(resolve => setTimeout(resolve,0));

describe('unread attention badges', () => {
  it('recognizes IRC nick addressing, explicit mentions and configured highlights, not substring collisions', () => {
    for (const body of ['Iggy: hello','iggy, hello','hello @Iggy!','\x02@Iggy\x0f']) expect(callsAttention(message(body),conversation)).toBe(true);
    for (const body of ['hello @Iggys','notiggy: hello','mail@iggy.example']) expect(callsAttention(message(body),conversation)).toBe(false);
    expect(callsAttention(message('Iggy:',{mine:true}),conversation)).toBe(false);
    expect(callsAttention(message('custom word',{highlighted:true}),conversation)).toBe(true);
  });
  it('checks unread pages once without marking read and ignores already-read highlights', async () => {
    let value = new Set<string>(); const requests:any[]=[];
    const tracker = new UnreadHighlights(ids => value = ids);
    const transport = { request:async (request:any):Promise<Response> => { requests.push(request); return {kind:'history',page:{messages:[message('@Iggy'),message('one'),message('two')],before:null}}; } };
    tracker.update(snapshot(),transport); await flush();
    expect(value.size).toBe(0); tracker.update(snapshot(),transport); await flush(); expect(requests).toHaveLength(1);
    tracker.update(snapshot([{...conversation,unread:3}]),transport); await flush(); expect([...value]).toEqual(['a']);
    expect(requests.every(r => r.kind==='history')).toBe(true);
    tracker.update(snapshot([{...conversation,unread:0}]),transport); expect(value.size).toBe(0);
  });
  it('drops delayed responses after lock/profile replacement', async () => {
    let value = new Set<string>(), release:(value:Response)=>void = () => {};
    const tracker = new UnreadHighlights(ids => value = ids);
    tracker.update(snapshot(), { request:() => new Promise(resolve => release=resolve) });
    tracker.clear();
    release({kind:'history',page:{messages:[message('@Iggy')],before:null}}); await flush();
    expect(value.size).toBe(0);
  });
});
