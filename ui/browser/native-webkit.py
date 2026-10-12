#!/usr/bin/env python3
"""Render and exercise the shared UI in native Linux GTK3/WebKitGTK 4.1.

Run the local fixture server first. This qualifies native webview rendering,
not a signed installer, network delivery or the Tauri window-command bridge.
Uses an ephemeral web context and writes source-bound screenshots/check results.
"""
import argparse
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, GLib, WebKit2  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:1438/?native-shell')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--source', required=True)
parser.add_argument('--width', type=int, default=1100)
args = parser.parse_args()
url = urlsplit(args.url)
if url.scheme != 'http' or url.hostname != '127.0.0.1' or not 320 <= args.width <= 1920:
    parser.error('Use a loopback HTTP fixture and a width between 320 and 1920')
args.output.mkdir(parents=True, exist_ok=True)
report = {'source': args.source, 'engine': '.'.join(str(part()) for part in (
    WebKit2.get_major_version, WebKit2.get_minor_version, WebKit2.get_micro_version)),
    'width': args.width, 'checks': [], 'screenshots': [], 'passed': False}
window = Gtk.Window(title='GChat — isolated UX evaluation')
window.set_default_size(args.width, 720)
view = WebKit2.WebView.new_with_context(WebKit2.WebContext.new_ephemeral())
window.add(view)
deadline = time.monotonic() + 90
finished = False


def finish(error=None):
    global finished
    if finished:
        return
    finished = True
    report['passed'] = error is None
    if error:
        report['error'] = str(error)
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    window.destroy()
    Gtk.main_quit()


def evaluate(script, callback):
    view.evaluate_javascript('JSON.stringify((() => {' + script + '})())', -1, None, None, None,
                             lambda webview, result, data=None: complete_json(webview, result, callback), None)


def complete_json(webview, result, callback):
    try:
        value = webview.evaluate_javascript_finish(result)
        callback(json.loads(value.to_string()))
    except Exception as error:
        finish(error)


def check(name, expression, next_step):
    def checked(value):
        report['checks'].append({'name': name, 'passed': value is True})
        if value is not True:
            finish('Failed: ' + name)
        else:
            next_step()
    evaluate('return !!(' + expression + ');', checked)


def capture(name, next_step):
    def captured(webview, result, _data=None):
        try:
            surface = webview.get_snapshot_finish(result)
            surface.write_to_png(str(args.output / (name + '.png')))
            report['screenshots'].append(name + '.png')
            next_step()
        except Exception as error:
            finish(error)
    view.get_snapshot(WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE,
                      None, captured, None)


def after_render(callback):
    GLib.timeout_add(350, lambda: (callback(), False)[1])


def accepted():
    check('confirmed message preserves multiline body',
          "document.querySelector('.message.mine .body')?.textContent === 'Native WebKit\\n  preserved spacing 日本語 👋'",
          lambda: capture('confirmed', scrollback))


def pending():
    check('pending uses the shared message renderer',
          "document.querySelector('.message.mine')?.textContent.includes('Sending…')",
          lambda: capture('pending', lambda: evaluate(
              'window.fixture.releaseSends(); return true;', lambda _: after_render(accepted))))


def send():
    evaluate(r"""
      window.fixture.holdSends();
      const input = document.querySelector('.composer textarea');
      input.value = 'Native WebKit\n  preserved spacing 日本語 👋';
      input.dispatchEvent(new Event('input', {bubbles:true}));
      setTimeout(() => document.querySelector('.send').click(), 0);
      return true;
    """, lambda _: after_render(pending))


def scrollback():
    evaluate('window.fixture.seedMessages(80); return true;', lambda _: after_render(scroll))


def scroll():
    evaluate("""
      const log = document.querySelector('.transcript');
      log.dispatchEvent(new WheelEvent('wheel',{deltaY:-500})); log.scrollTop -= 500;
      log.dispatchEvent(new Event('scroll'));
      window.nativeTop = log.scrollTop;
      window.fixture.receive('Incoming while reading'); return true;
    """, lambda _: after_render(lambda: check('incoming messages preserve scrollback',
        "Math.abs(document.querySelector('.transcript').scrollTop-window.nativeTop)<3",
        lambda: capture('scrollback', zoom_dialog))))


def zoom_dialog():
    evaluate("document.documentElement.style.zoom='2'; return true;", lambda _: after_render(
        lambda: check('text zoom keeps the composer on screen',
            "document.querySelector('.composer').getBoundingClientRect().bottom<=innerHeight",
            lambda: evaluate("document.querySelector('[aria-label=\"Help and commands\"]').click(); return true;",
                lambda _: after_render(lambda: check('zoomed dialog back control is reachable',
                    "(() => { const r=document.querySelector('dialog[open] [data-screen-back]').getBoundingClientRect(); return r.top>=0 && r.bottom<=innerHeight && r.left>=0 && r.right<=innerWidth; })()",
                    lambda: capture('zoomed-help', lambda: finish())))))))


def initial():
    check('viewport fits and composer is reachable',
          "document.documentElement.scrollWidth<=innerWidth && document.querySelector('.composer').getBoundingClientRect().bottom<=innerHeight",
          lambda: capture('workspace', send))


def wait_ready():
    if finished:
        return False
    if time.monotonic() > deadline:
        finish('Native UI deadline exceeded')
        return False
    evaluate("return !!window.fixture && document.querySelector('.active-title')?.textContent === '#general' && document.fonts.status === 'loaded';",
             lambda value: initial() if value else GLib.timeout_add(100, wait_ready))
    return False


window.connect('delete-event', lambda *_: finish('Window closed before completion'))
window.show_all()
view.load_uri(args.url)
GLib.timeout_add(200, wait_ready)
GLib.timeout_add_seconds(90, lambda: (finish('Native UI deadline exceeded'), False)[1])
Gtk.main()
print(json.dumps(report, indent=2))
sys.exit(0 if report['passed'] else 1)
