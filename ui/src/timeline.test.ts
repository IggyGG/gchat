import { it, expect } from 'vitest';
import { groupActivity, operationLabel } from './timeline';
import type { Activity } from './api';
import type { OperationResult } from './operation-results';

it('does not group through a message, an actionable event, a long gap or midnight',()=>{
  const event=(id:string,timestamp:number,kind='join')=>({id,timestamp,activity:{id,timestamp,kind,text:id,conversation:'a'} as Activity});
  const midnight=new Date(2026,9,12).getTime()/1000;
  const result=groupActivity([
    event('1',midnight-2),event('2',midnight-1),event('3',midnight),
    {id:'message',timestamp:midnight+1,activity:undefined},event('4',midnight+2),
    event('failed',midnight+3,'send_failed'),event('5',midnight+4),event('6',midnight+200),
  ]);
  expect(result.map(row=>row.activities?.map(a=>a.id)??[row.id])).toEqual([['1','2'],['3'],['message'],['4'],['failed'],['5'],['6']]);
});

it('an unknown result says checking only while an actual check is in progress',()=>{
  const result={state:'unknown',action:'/invite'} as OperationResult;
  expect(operationLabel(result)).toBe('Outcome unconfirmed');
  expect(operationLabel(result,true)).toBe('Checking…');
});
