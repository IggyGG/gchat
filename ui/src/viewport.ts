/** WebKit may label a synthesized touch click as mouse; prefer its initiating pointer. */
export function isTouchActivation(event: { detail: number; pointerType?: string } | undefined, coarse: boolean, initiatingPointer?: string) {
  if (!event || event.detail === 0) return false;
  const pointerType = initiatingPointer || event.pointerType;
  if (pointerType) return pointerType === 'touch' || pointerType === 'pen';
  return event.detail > 0 && coarse;
}

/** Follow the keyboard viewport on touch devices without resizing during pinch zoom. */
export function fitVisualViewport(node: HTMLElement) {
  const viewport = window.visualViewport;
  if (!viewport) return;
  const touch = window.matchMedia('(pointer: coarse)');
  const properties = ['--gchat-viewport-height', '--gchat-viewport-top', '--gchat-viewport-position'];
  const previous = properties.map(name => node.style.getPropertyValue(name));
  const restore = () => properties.forEach((name, index) => {
    if (previous[index]) node.style.setProperty(name, previous[index]);
    else node.style.removeProperty(name);
  });
  const update = () => {
    if (!touch.matches) { restore(); return; }
    // Zoom changes the visible rectangle, not the app's keyboard layout.
    if (!Number.isFinite(viewport.scale) || Math.abs(viewport.scale - 1) > 0.01
      || !Number.isFinite(viewport.height) || viewport.height <= 0
      || !Number.isFinite(viewport.offsetTop) || viewport.offsetTop < 0) return;
    node.style.setProperty('--gchat-viewport-height', `${viewport.height}px`);
    node.style.setProperty('--gchat-viewport-top', `${viewport.offsetTop}px`);
    node.style.setProperty('--gchat-viewport-position', 'fixed');
  };
  viewport.addEventListener('resize', update);
  viewport.addEventListener('scroll', update);
  window.addEventListener('resize', update);
  touch.addEventListener('change', update);
  update();
  return { destroy() {
    viewport.removeEventListener('resize', update);
    viewport.removeEventListener('scroll', update);
    window.removeEventListener('resize', update);
    touch.removeEventListener('change', update);
    restore();
  } };
}
