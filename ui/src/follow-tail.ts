/** Follow layout changes without mistaking them for a deliberate scroll back. */
export function followTail(node: HTMLElement, options: { following: boolean; scope: string | null; changed: (following: boolean) => void }) {
  let value = options, frame = 0, userUntil = 0, lastTop = node.scrollTop;
  let anchor: { key: string; offset: number } | undefined;
  const remember = () => {
    const top = node.getBoundingClientRect().top;
    const item = [...node.querySelectorAll<HTMLElement>('[data-timeline-key]')].find(el => el.getBoundingClientRect().bottom > top);
    anchor = item ? { key: item.dataset.timelineKey!, offset: item.getBoundingClientRect().top - top } : undefined;
  };
  const settle = () => {
    frame = 0;
    if (value.following) node.scrollTop = node.scrollHeight;
    else if (anchor) {
      const item = [...node.querySelectorAll<HTMLElement>('[data-timeline-key]')].find(el => el.dataset.timelineKey === anchor!.key);
      if (item) {
        const wanted = node.scrollTop + item.getBoundingClientRect().top - node.getBoundingClientRect().top - anchor.offset;
        node.scrollTop = wanted;
        // Some engines quantize scrollTop. Pick the nearest representable pixel
        // instead of accumulating their downward rounding after a font change.
        if (Math.abs(node.scrollTop - wanted) > 0.5) node.scrollTop = Math.round(wanted);
      }
    }
    lastTop = node.scrollTop;
  };
  const schedule = () => { if (!frame) frame = requestAnimationFrame(settle); };
  // A viewport adjustment can emit scroll events inside an earlier wheel's
  // grace period. Those layout events must not replace the reader's anchor.
  const resized = () => { userUntil = 0; schedule(); };
  const intent = () => { userUntil = performance.now() + 1000; };
  const anchorHere = () => { value = { ...value, following:false }; userUntil = 0; lastTop = node.scrollTop; remember(); };
  const key = (event: KeyboardEvent) => { if (['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '].includes(event.key)) intent(); };
  const scrolled = () => {
    if (performance.now() < userUntil && Math.abs(node.scrollTop - lastTop) > 1) {
      const following = node.scrollHeight - node.scrollTop - node.clientHeight < 35;
      value.changed(following); value = { ...value, following };
      if (!following) remember(); else anchor = undefined;
    }
    lastTop = node.scrollTop;
  };
  window.addEventListener('resize', resized);
  const resize = new ResizeObserver(schedule);
  resize.observe(node);
  if (node.firstElementChild) resize.observe(node.firstElementChild);
  node.addEventListener('wheel', intent, { passive:true });
  node.addEventListener('touchstart', intent, { passive:true });
  node.addEventListener('touchmove', intent, { passive:true });
  node.addEventListener('pointerdown', intent);
  node.addEventListener('keydown', key);
  node.addEventListener('scroll', scrolled, { passive:true });
  node.addEventListener('gchat-anchor-here', anchorHere);
  schedule();
  return {
    update(next: typeof options) {
      if (next.following && !value.following) userUntil = 0;
      if (next.scope !== value.scope) { anchor = undefined; userUntil = 0; }
      value = next;
      if (value.following) anchor = undefined;
      schedule();
    },
    destroy() {
      window.removeEventListener('resize', resized);
      resize.disconnect(); cancelAnimationFrame(frame);
      node.removeEventListener('gchat-anchor-here',anchorHere);
      node.removeEventListener('wheel',intent); node.removeEventListener('touchstart',intent); node.removeEventListener('touchmove',intent);
      node.removeEventListener('pointerdown',intent); node.removeEventListener('keydown',key); node.removeEventListener('scroll',scrolled);
    }
  };
}
