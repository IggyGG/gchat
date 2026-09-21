import { afterEach, describe, expect, it, vi } from 'vitest';
import { fitVisualViewport, isTouchActivation } from './viewport';

afterEach(() => vi.unstubAllGlobals());

function setup(coarse = true) {
  const viewport = Object.assign(new EventTarget(), { height: 844, offsetTop: 0, scale: 1 });
  const pointer = Object.assign(new EventTarget(), { matches: coarse });
  const host = Object.assign(new EventTarget(), { visualViewport: viewport, matchMedia: () => pointer });
  const values = new Map<string, string>();
  const node = { style: {
    getPropertyValue: (name: string) => values.get(name) ?? '',
    setProperty: (name: string, value: string) => { values.set(name, value); },
    removeProperty: (name: string) => { values.delete(name); },
  } } as unknown as HTMLElement;
  vi.stubGlobal('window', host);
  return { viewport, pointer, host, node, values };
}

describe('touch keyboard viewport', () => {
  it('distinguishes touch navigation from hardware keyboard and mouse activation', () => {
    expect(isTouchActivation({ detail: 1, pointerType: 'touch' }, false)).toBe(true);
    expect(isTouchActivation({ detail: 1, pointerType: 'pen' }, false)).toBe(true);
    expect(isTouchActivation({ detail: 1 }, true)).toBe(true);
    expect(isTouchActivation({ detail: 0 }, true)).toBe(false);
    expect(isTouchActivation({ detail: 1, pointerType: 'mouse' }, true)).toBe(false);
    expect(isTouchActivation(undefined, true)).toBe(false);
  });
  it('follows keyboard movement and rotation, ignores pinch zoom and removes listeners', () => {
    const { viewport, host, node, values } = setup();
    const action = fitVisualViewport(node);
    expect(values.get('--gchat-viewport-height')).toBe('844px');
    Object.assign(viewport, { height: 360, offsetTop: 24 });
    viewport.dispatchEvent(new Event('resize'));
    expect(values.get('--gchat-viewport-height')).toBe('360px');
    expect(values.get('--gchat-viewport-top')).toBe('24px');
    Object.assign(viewport, { height: 180, offsetTop: 80, scale: 2 });
    viewport.dispatchEvent(new Event('scroll'));
    expect(values.get('--gchat-viewport-height')).toBe('360px');
    expect(values.get('--gchat-viewport-top')).toBe('24px');
    Object.assign(viewport, { height: 390, offsetTop: 0, scale: 1 });
    host.dispatchEvent(new Event('resize'));
    expect(values.get('--gchat-viewport-height')).toBe('390px');
    action?.destroy();
    viewport.height = 200;
    viewport.dispatchEvent(new Event('resize'));
    host.dispatchEvent(new Event('resize'));
    expect(values.size).toBe(0);
  });

  it('leaves desktop layout unchanged and restores CSS when pointer capability changes', () => {
    const { viewport, pointer, node, values } = setup(false);
    values.set('--gchat-viewport-height', '90dvh');
    const action = fitVisualViewport(node);
    expect(values.get('--gchat-viewport-height')).toBe('90dvh');
    expect(values.has('--gchat-viewport-position')).toBe(false);
    pointer.matches = true;
    pointer.dispatchEvent(new Event('change'));
    expect(values.get('--gchat-viewport-height')).toBe('844px');
    viewport.height = 0;
    viewport.dispatchEvent(new Event('resize'));
    expect(values.get('--gchat-viewport-height')).toBe('844px');
    pointer.matches = false;
    pointer.dispatchEvent(new Event('change'));
    expect(values.get('--gchat-viewport-height')).toBe('90dvh');
    expect(values.has('--gchat-viewport-position')).toBe(false);
    action?.destroy();
  });

  it('uses normal CSS when the browser has no visual viewport API', () => {
    vi.stubGlobal('window', { visualViewport: null });
    expect(fitVisualViewport({} as HTMLElement)).toBeUndefined();
  });
});
