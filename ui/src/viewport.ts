/** WebKit may label a synthesized touch click as mouse; prefer its initiating pointer. */
export function isTouchActivation(event: { detail: number; pointerType?: string } | undefined, coarse: boolean, initiatingPointer?: string) {
  if (!event || event.detail === 0) return false;
  const pointerType = initiatingPointer || event.pointerType;
  if (pointerType) return pointerType === 'touch' || pointerType === 'pen';
  return event.detail > 0 && coarse;
}

/** Fit keyboard and CSS text-zoom viewports without following pinch zoom. */
export function fitVisualViewport(node: HTMLElement) {
  const viewport = window.visualViewport;
  if (!viewport) return;
  const touch = window.matchMedia('(pointer: coarse)');
  const properties = ['--gchat-viewport-height', '--gchat-viewport-top', '--gchat-viewport-position', '--gchat-viewport-width'];
  const previous = properties.map(name => node.style.getPropertyValue(name));
  const restore = () => properties.forEach((name, index) => {
    if (previous[index]) node.style.setProperty(name, previous[index]);
    else node.style.removeProperty(name);
  });
  const update = () => {
    const declaredZoom = Number.parseFloat(window.getComputedStyle(document.documentElement).zoom);
    const zoom = Number.isFinite(declaredZoom) && declaredZoom > 0 ? declaredZoom : 1;
    if (!touch.matches && zoom === 1) { restore(); return; }
    // Zoom changes the visible rectangle, not the app's keyboard layout.
    if (!Number.isFinite(viewport.scale) || Math.abs(viewport.scale - 1) > 0.01
      || !Number.isFinite(viewport.height) || viewport.height <= 0
      || !Number.isFinite(viewport.offsetTop) || viewport.offsetTop < 0) return;
    node.style.setProperty('--gchat-viewport-height', `${viewport.height / zoom}px`);
    node.style.setProperty('--gchat-viewport-top', `${viewport.offsetTop / zoom}px`);
    node.style.setProperty('--gchat-viewport-width', `${(viewport.width ?? window.innerWidth) / zoom}px`);
    node.style.setProperty('--gchat-viewport-position', touch.matches ? 'fixed' : 'relative');
  };
  const rootStyle = new MutationObserver(update);
  rootStyle.observe(document.documentElement, { attributes:true, attributeFilter:['style','class'] });
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
    rootStyle.disconnect();
    restore();
  } };
}
