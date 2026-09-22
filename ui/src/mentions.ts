/** Local roster completion: typing a mention never performs a network request. */
export function mentionSuggestions(text: string, caret: number, names: string[]) {
  const prefix = text.slice(0, caret);
  const match = /(?:^|[\s([{])@([^\s@.,;:!?()[\]{}<>]*)$/u.exec(prefix);
  if (!match) return null;
  const start = caret - match[1].length - 1;
  const tail = /^[^\s@.,;:!?()[\]{}<>]*/u.exec(text.slice(caret))![0];
  const query = match[1].toLocaleLowerCase();
  const items = [...new Set(names)].filter(name => name && !/[\s@.,;:!?()[\]{}<>]/u.test(name) && name.toLocaleLowerCase().startsWith(query)).slice(0, 12);
  return items.length ? { start, end: caret + tail.length, items } : null;
}
export function insertMention(text: string, start: number, end: number, name: string) {
  const suffix = text.slice(end);
  const insertion = '@' + name + (!suffix || !/^[\s.,;:!?()[\]{}<>]/u.test(suffix) ? ' ' : '');
  return { text: text.slice(0, start) + insertion + suffix, caret: start + insertion.length };
}
