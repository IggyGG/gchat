"""Real accessibility/picker driver for a newly created, owned Android AVD.

UI hierarchies and invitation values stay in memory. No application endpoint,
debug build, WebView instrumentation or personal-device operation is used.
"""
import csv
import hashlib
import io
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET

from mobile_acceptance_inputs import require
from release_network_canary import module

android = module('android-build')


def labels(node):
    return [value for child in node.iter('node')
            for value in (child.get('text', ''), child.get('content-desc', '')) if value]


def owned_channel(node):
    return any(re.fullmatch(r'#?\s*mobile-release(?:\s+\d+)?', node.get(key, ''))
               for key in ('text', 'content-desc'))


def named_control(node, prefix):
    return any(node.get(key, '').startswith(prefix) for key in ('text', 'content-desc'))


def launcher_anr_close(tree):
    def title(node):
        if node.get('package') != 'android': return False
        for key in ('text', 'content-desc'):
            value = node.get(key, '').translate({ord(c): None for c in '\u2068\u2069\u200e\u200f'})
            if value.replace('\u2019', "'").strip() == "Pixel Launcher isn't responding": return True
        return False
    if not any(title(node) for node in tree.iter('node')): return None
    return next((node for node in tree.iter('node') if node.get('package') == 'android'
                 and node.get('resource-id') == 'android:id/aerr_close' and android.ui_bounds(node)), None)


def completed_file_row(tree, name, known_names):
    for node in reversed(list(tree.iter('node'))):
        values = labels(node)
        if name in values and set(values) & known_names == {name}:
            if any(' · complete · ' in value for value in values):
                return True
    return False


def editable_composer(tree):
    fields = [node for node in tree.iter('node') if node.get('package') == android.PACKAGE
              and node.get('class') == 'android.widget.EditText'
              and node.get('password') != 'true' and android.ui_bounds(node)]
    return fields[0] if len(fields) == 1 else None


def invitation_nickname(tree):
    nodes = list(tree.iter('node'))
    preview = any(named_control(node, 'Join #mobile-release on ') for node in nodes)
    join = any(node.get(key) == 'Join' for node in nodes for key in ('text', 'content-desc'))
    return editable_composer(tree) if preview and join else None


def invitation_form(tree, expected=None):
    nodes = list(tree.iter('node'))
    owned = [node for node in nodes if node.get('package') == android.PACKAGE]
    if not any(AndroidUI.text('Invitation')(node) for node in owned): return None
    if not any(AndroidUI.text('Continue')(node) for node in owned): return None
    field = editable_composer(tree)
    allowed = ('', 'Paste an invitation') if expected is None else ('', 'Paste an invitation', expected)
    return field if field is not None and field.get('text', '') in allowed else None


def message_bodies(values, known_bodies):
    # Android can merge inline timestamp/nickname/body text into one label.
    # Match complete canary tokens, never prefixes inside another message.
    return {body for body in known_bodies if any(re.search(
        r'(?<![A-Za-z0-9_-])' + re.escape(body) + r'(?![A-Za-z0-9_-])', value)
        for value in (' '.join(value.split()) for value in values))}


def delivery_row(tree, body, known_bodies):
    # A delivered suffix elsewhere in the transcript cannot qualify this send.
    # Require one smallest message subtree containing exactly this test body.
    for node in reversed(list(tree.iter('node'))):
        values = labels(node)
        if any(value.strip() == '· delivered' or value.rstrip().endswith(' · delivered') for value in values):
            if message_bodies(values, known_bodies) == {body}:
                return True
    return False


def pixel_lines(tsv, bounds, excluded=()):
    """Recognized words wholly inside the owned, visible transcript only."""
    x1, y1, x2, y2 = bounds
    words = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter='\t'):
        if row['level'] != '5' or not row['text'].strip(): continue
        x, y, width, height = (int(row[key]) for key in ('left', 'top', 'width', 'height'))
        if width <= 0 or height <= 0 or not (x1 <= x and y1 <= y and x+width <= x2 and y+height <= y2): continue
        # Floating native controls can cover the transcript's rectangle without
        # belonging to its text. Their actual accessibility bounds, rather than
        # recognition guesses, exclude occluded pixels from message matching.
        if any(x < right and x+width > left and y < bottom and y+height > top
               for left, top, right, bottom in excluded): continue
        words.append((x, y, width, height, row['text']))
    # Sparse OCR assigns different block/line IDs to words on the same physical
    # row, especially across the nickname/body/status fonts. Those IDs cannot
    # define a rendered message line. Only geometrically overlapping words can
    # share a row; separate message/status rows remain separate.
    lines = []
    for word in sorted(words, key=lambda word: (word[1], word[0])):
        x, y, width, height, value = word
        candidates = []
        for index, line in enumerate(lines):
            top = min(w[1] for w in line)
            bottom = max(w[1]+w[3] for w in line)
            overlap = min(bottom, y+height)-max(top, y)
            if overlap >= 0.6*min(height, bottom-top):
                candidates.append((abs((top+bottom)/2-(y+height/2)), index))
        if candidates:
            lines[min(candidates)[1]].append(word)
        else:
            lines.append([word])
    return sorted([{'text': ' '.join(word[4] for word in sorted(words)),
        'top': min(word[1] for word in words), 'bottom': max(word[1]+word[3] for word in words)}
        for words in lines], key=lambda line: line['top'])


def pixel_message_spans(lines, body):
    for start in range(len(lines)):
        text = ''
        for end in range(start, min(len(lines), start+8)):
            line = lines[end]
            if end > start:
                previous = lines[end-1]
                if not (previous['top'] <= line['top'] <= previous['bottom'] +
                        # Short lowercase words expose only x-height glyphs,
                        # not the CSS line box. Keep ordinary leading while
                        # still refusing distant rows or unrelated text.
                        2.5*(previous['bottom']-previous['top'])): break
            text += ' ' + line['text']
            if message_bodies([text], {body}):
                suffix = ' '.join(text.split()).split(body, 1)[1]
                if re.fullmatch(r'[^\w]*(?:delivered[^\w]*)?', suffix):
                    yield start, end, text
                break


def pixel_delivered(lines, body, known_bodies):
    for start, index, text in pixel_message_spans(lines, body):
        line = lines[index]
        if message_bodies([text], known_bodies) != {body}: continue
        # A status before the body cannot acknowledge this message.
        suffix = ' '.join(text.split()).split(body, 1)[1]
        if re.fullmatch(r'[^\w]*delivered[^\w]*', suffix): return True
        # A wrapped receipt must be the next line and contain only its status.
        if index+1 < len(lines):
            following = lines[index+1]
            if re.fullmatch(r'[^\w]*delivered[^\w]*', following['text']) and (
                # The receipt uses a smaller font on the next inherited line
                # box. Its glyph bounds do not measure that line's pitch.
                line['top'] <= following['top'] <= line['bottom']+2.5*(line['bottom']-line['top'])):
                return True
    return False


def pixel_body_layout(lines, body):
    """Numeric word positions only; never retain rendered text or canary words."""
    words = body.split()
    result = []
    for row, line in enumerate(lines[:48]):
        positions = sorted((match.start(), index) for index, word in enumerate(words)
            for match in re.finditer(r'(?<!\w)'+re.escape(word)+r'(?!\w)', line['text']))
        if positions:
            result.append({'row': row, 'top': line['top'], 'bottom': line['bottom'],
                'positions': [list(value) for value in positions[:24]]})
    return result


def pixel_transfer_progress(lines, name, size, known_names):
    """Exact filename, its transfer status and byte counter in adjacent rows."""
    statuses = {'downloading', 'waiting for peers', 'paused', 'Downloaded · shared while unlocked'}
    for index, title in enumerate(lines):
        if title['text'] != name or index + 2 >= len(lines):
            continue
        status = lines[index + 1]
        if status['text'] not in statuses or status['top'] > title['bottom'] + 3 * (title['bottom']-title['top']):
            continue
        text = ''
        previous = status
        for counter in lines[index+2:index+5]:
            if counter['top'] > previous['bottom'] + 5 * (previous['bottom']-previous['top']):
                break
            if any(other in counter['text'] for other in known_names):
                break
            text = (text + ' ' + counter['text']).strip()
            match = re.fullmatch(r'([0-9]+(?:,[0-9]{3})*) / ([0-9]+(?:,[0-9]{3})*) bytes verified', text)
            if match:
                value, total = (int(part.replace(',', '')) for part in match.groups())
                if total == size and 0 <= value <= size:
                    return value
                break
            previous = counter
    return None


def system_picker_control(node, values):
    return node.get('package') in ('com.android.documentsui', 'com.google.android.documentsui') and any(
        node.get(key) in values for key in ('text', 'content-desc'))


class AndroidUI:
    dump = '/sdcard/gchat-mobile-acceptance-ui.xml'

    def __init__(self, serial, output, passphrase, deadline):
        match = re.fullmatch(r'emulator-(\d{4})', serial)
        require(match and 5554 <= int(match[1]) <= 5682 and int(match[1]) % 2 == 0,
                'owned explicit Android emulator required')
        sdk = android.sdk(require_ndk=False)
        self.adb = [str(sdk / 'platform-tools/adb'), '-s', serial]
        self.output, self.passphrase, self.deadline = output, passphrase, deadline
        self.installed = False
        self.uid = None
        self.names, self.bodies = set(), set()
        self.exports = []
        self.ui_observation = {'attempts':0, 'errors':0}
        self.input_started = False
        require(self.shell('getprop', 'ro.kernel.qemu') == '1', 'physical device refused')
        expected = 'gchat-release-fixture-' + serial.removeprefix('emulator-')
        require(self.command('emu', 'avd', 'name').splitlines()[0] == expected,
                'emulator was not created by this test driver')
        require(not self.shell('pm', 'path', android.PACKAGE, absent=True),
                'GChat already installed; fresh owned AVD required')
        android.root_emulator(self.adb, output / 'adb-root.json')
        android.prepare_emulator_user(self.shell)
        require(self.shell('getprop', 'ro.product.cpu.abi') == 'x86_64'
                and int(self.shell('getprop', 'ro.build.version.sdk')) >= 26,
                'Android test ABI/API differs')
        # Preserve the 320x640 logical viewport with normal phone pixel density.
        # Tiny physical glyphs are insufficient for exact native OCR tokens.
        self.shell('wm', 'size', '720x1440')
        self.shell('wm', 'density', '360')
        self.ui_observation['display_size'] = [720, 1440]
        self.ui_observation['display_density'] = 360

    def command(self, *args, binary=False, absent=False):
        left = min(120, self.deadline() - time.monotonic())
        require(left > 0, 'original mobile journey deadline')
        result = subprocess.run([*self.adb, *map(str, args)], capture_output=True, timeout=left)
        if absent and result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
            return b'' if binary else ''
        # Never include a command, stderr or hierarchy in an exception: native
        # intent/input arguments can contain the private canary invitation.
        require(result.returncode == 0, 'owned Android command failed')
        return result.stdout if binary else result.stdout.decode().strip()

    def shell(self, *args, absent=False, absent_ok=False):
        # Shared disposable-device setup uses absent_ok for optional packages.
        return self.command('shell', *args, absent=absent or absent_ok)

    def tree(self):
        self.ui_observation['attempts'] += 1
        # One ADB round trip; removal and successful dump remain prerequisites
        # for reading XML, so an old hierarchy can never satisfy a new check.
        path = shlex.quote(self.dump)
        script = f'rm -f {path} && uiautomator dump {path} >/dev/null && cat {path}'
        try:
            tree = ET.fromstring(self.shell('sh', '-c', shlex.quote(script)))
        except (ValueError, ET.ParseError) as error:
            self.ui_observation.update(errors=self.ui_observation['errors']+1, last_error=type(error).__name__)
            return ET.Element('hierarchy')
        close = launcher_anr_close(tree)
        if close is not None:
            count = self.ui_observation.get('launcher_anr_dismissed', 0)
            require(count < 2, 'owned Android launcher repeatedly unresponsive')
            self.tap(close)
            self.ui_observation['launcher_anr_dismissed'] = count + 1
            return ET.Element('hierarchy')
        nodes = [node for node in tree.iter('node') if node.get('package') == android.PACKAGE]
        # Fixed control counts diagnose startup without retaining private UI text.
        self.ui_observation.update(application_nodes=len(nodes),
            password_fields=sum(node.get('password') == 'true' for node in nodes),
            create_identity=sum(self.text('Create identity')(node) for node in nodes),
            reconnect=sum(self.text('Reconnect')(node) for node in nodes),
            public_controls={'network':sum(named_control(node, 'Network:') for node in nodes),
                'files':sum(named_control(node, 'Files:') for node in nodes),
                'send':sum(self.text('Send')(node) for node in nodes),
                'connect_to_gchat':sum(self.text('Connect to GChat')(node) for node in nodes),
                'close_dialog':sum(self.text('Close dialog')(node) for node in nodes),
                'close_details':sum(self.text('Close details')(node) for node in nodes),
                'nickname':sum(self.text('Your nickname in this channel')(node) for node in nodes),
                'invitation_preview':sum(named_control(node, 'Join #mobile-release on ') for node in nodes),
                'join':sum(self.text('Join')(node) for node in nodes),
                'continue':sum(self.text('Continue')(node) for node in nodes),
                'validating':sum(self.text('Validating…')(node) for node in nodes),
                'notifications':sum(self.text('Notifications')(node) for node in nodes)})
        return tree

    def until(self, fn, timeout=60):
        end = min(self.deadline(), time.monotonic() + timeout)
        while time.monotonic() < end:
            value = fn()
            if value:
                require(time.monotonic() <= end, 'late mobile UI observation')
                return value
            time.sleep(0.4)
        raise TimeoutError('original mobile UI observation deadline')

    def node(self, predicate, timeout=60):
        def find():
            nodes = list(self.tree().iter('node'))
            matches = [node for node in nodes if predicate(node)]
            visible = next((node for node in matches if android.ui_bounds(node)), None)
            if visible is None and matches:
                # The installed lifecycle fixture already reveals fields below
                # the fold this way. Keep the original observation deadline.
                bounds = next((android.ui_bounds(node) for node in nodes
                               if node.get('package') == android.PACKAGE and android.ui_bounds(node)), None)
                require(bounds is not None, 'owned Android UI has no visible application surface')
                x1, y1, x2, y2 = bounds
                self.shell('input', 'swipe', (x1+x2)//2, y1+(y2-y1)*4//5,
                           (x1+x2)//2, y1+(y2-y1)//3, '250')
            return visible
        # ElementTree elements have false truth values when childless.
        return self.until(lambda: (node,) if (node := find()) is not None else None, timeout)[0]

    @staticmethod
    def text(value):
        return lambda node: node.get('text') == value or node.get('content-desc') == value

    def click(self, value):
        node = self.node(self.text(value))
        self.tap(node)

    def tap(self, node):
        x1, y1, x2, y2 = android.ui_bounds(node)
        self.shell('input', 'tap', (x1 + x2) // 2, (y1 + y2) // 2)

    def scroll_to_top(self):
        bounds = [android.ui_bounds(node) for node in self.tree().iter('node')
                  if node.get('package') == android.PACKAGE and android.ui_bounds(node)]
        require(bounds, 'owned Android application viewport unavailable')
        x1, y1, x2, y2 = max(bounds, key=lambda box: (box[2]-box[0])*(box[3]-box[1]))
        for _ in range(2):
            self.shell('input', 'swipe', (x1+x2)//2, y1+(y2-y1)//4,
                       (x1+x2)//2, y1+3*(y2-y1)//4, '250')

    def type(self, node, value, system_export=False, replace=False):
        package = node.get('package')
        require(package == android.PACKAGE or (system_export and package in
            ('com.android.documentsui', 'com.google.android.documentsui')),
            'native input requires the owned application or system export picker')
        require(not replace or (system_export and package in
            ('com.android.documentsui', 'com.google.android.documentsui')),
            'replacement is restricted to the actual system export filename')
        self.ui_observation['input_target_bounds'] = android.ui_bounds(node)
        self.tap(node)
        # WebView focus and the IME arrive asynchronously. Pressing Back before
        # the keyboard appears closes the app instead of dismissing the IME.
        android.wait_keyboard(self.shell, True)
        self.until(lambda: any(child.get('package') == package
            and child.get('class') == 'android.widget.EditText' and child.get('focused') == 'true'
            and child.get('password', 'false') == node.get('password', 'false')
            and all(child.get(key, '') == node.get(key, '') for key in ('resource-id', 'content-desc'))
            for child in self.tree().iter('node')), 10)
        self.input_started = True
        if replace:
            def empty():
                fields = [child for child in self.tree().iter('node') if child.get('package') == package
                    and child.get('class') == 'android.widget.EditText' and child.get('focused') == 'true'
                    and all(child.get(key, '') == node.get(key, '') for key in ('resource-id', 'content-desc'))]
                require(len(fields) == 1, 'one focused system export filename required')
                text = fields[0].get('text', '')
                require(len(text) <= 255, 'unexpected system export filename')
                if not text: return True
                self.shell('input', 'keyevent', 'KEYCODE_MOVE_END')
                self.shell('input', 'keyevent', *(['KEYCODE_DEL'] * len(text)))
                return False
            # Clear only after focus and keyboard are ready, and observe the
            # actual empty value before entering the replacement. A delayed
            # deletion is reconciled within the same input operation.
            self.until(empty, 10)
        self.shell('input', 'text', shlex.quote(value.replace(' ', '%s')))
        def confirmed():
            fields = [child for child in self.tree().iter('node') if child.get('package') == package
                and child.get('class') == 'android.widget.EditText'
                and child.get('password', 'false') == node.get('password', 'false')
                and all(child.get(key, '') == node.get(key, '') for key in ('resource-id', 'content-desc'))]
            self.ui_observation['input_value'] = {'expected_length':len(value),'matching_fields':len(fields),
                'focused_fields':sum(child.get('focused') == 'true' for child in fields),
                'value_lengths':[len(child.get('text', '')) for child in fields],
                'exact_value_fields':sum(child.get('text') == value for child in fields),
                'case_changed_fields':sum(child.get('text', '').casefold() == value.casefold()
                    and child.get('text') != value for child in fields)}
            return any(child.get('focused') == 'true' and child.get('text') == value for child in fields)
        self.until(confirmed, 10)
        self.shell('input', 'keyevent', '4')
        android.wait_keyboard(self.shell, False)
        self.ui_observation['inputs_confirmed'] = self.ui_observation.get('inputs_confirmed', 0) + 1

    def no_listener(self):
        require(self.uid is not None, 'installed mobile UID unavailable')
        require(not android.listener_rows(self.shell('cat', '/proc/net/tcp', '/proc/net/tcp6'), self.uid),
                'outbound application opened a TCP listener')

    def install(self, item):
        if self.installed:
            self.stop()
        self.installed = True  # Partial installation also belongs to this AVD.
        self.command('install-multiple', '-r', '-d', '--no-streaming', *item['apks'])
        self.activity = item['activity']
        self.uid = android.installed_package_uid(
            self.shell('pm', 'list', 'packages', '-U', '--user', '0', android.PACKAGE))
        self.no_listener()

    def launch(self):
        self.shell('input', 'keyevent', 'KEYCODE_WAKEUP')
        self.shell('wm', 'dismiss-keyguard')
        result = self.shell('am', 'start', '-W', '-n', android.PACKAGE + '/' + self.activity)
        self.ui_observation['launch_status_ok'] = 'Status: ok' in result
        require(self.ui_observation['launch_status_ok'], 'owned Android activity did not start')

    def stop(self):
        self.shell('am', 'force-stop', android.PACKAGE)
        require(not self.shell('pidof', android.PACKAGE, absent=True),
                'owned application survived force-stop')

    def unlock(self, create=False):
        self.launch()
        button = 'Create identity' if create else 'Reconnect'
        try:
            self.node(self.text(button))
            # Revealing the submit button may hide the fields above the fold.
            # WebView can retain positive, clipped bounds under the header.
            self.scroll_to_top()
            for _ in range(2 if create else 1):
                field = self.node(lambda node: node.get('package') == android.PACKAGE
                                  and node.get('password') == 'true' and not node.get('text'))
                self.type(field, self.passphrase)
        except (TimeoutError, ValueError):
            # This fresh owned AVD has received no identity, passphrase, channel
            # or invitation. Never capture a reopened or populated app screen.
            if create and not self.input_started:
                try:
                    self.ui_observation['process_alive'] = bool(self.shell('pidof', android.PACKAGE, absent=True))
                    android.screenshot(self.adb, self.output.parent / 'fresh-startup.png')
                    self.ui_observation['fresh_startup_screen_retained'] = True
                except Exception as error:
                    self.ui_observation['startup_capture_error'] = type(error).__name__
            raise
        self.click(button)
        def unlocked():
            tree = self.tree()
            # The button becomes Opening… while the identity is still locked.
            # Require the actual post-unlock UI before delivering an OS link.
            return not any(self.text(button)(node) for node in tree.iter('node')) and (
                any(self.text('Connect to GChat')(node) for node in tree.iter('node'))
                or editable_composer(tree) is not None)
        self.until(unlocked, 120)
        self.no_listener()

    def join(self, invitation):
        require(invitation.startswith('gcoms:') and len(invitation.encode()) <= 180000,
                'bounded conversation invitation required')
        self.shell('am', 'start', '-W', '-a', 'android.intent.action.VIEW',
                   '-d', shlex.quote(invitation), android.PACKAGE)
        self.click('Review invitation')
        self.scroll_to_top()
        def enrollment_input():
            tree = self.tree()
            nickname = invitation_nickname(tree)
            if nickname is not None: return ('nickname', nickname)
            form = invitation_form(tree, invitation)
            fields = [node for node in tree.iter('node') if node.get('package') == android.PACKAGE
                      and node.get('class') == 'android.widget.EditText']
            self.ui_observation['invitation_form'] = {
                'editable_fields': len(fields),
                'empty_fields': sum(node.get('text', '') in ('', 'Paste an invitation') for node in fields),
                'exact_invitation_fields': sum(node.get('text') == invitation for node in fields),
                'invitation_label': any(self.text('Invitation')(node) for node in tree.iter('node')),
                'continue_enabled': any(self.text('Continue')(node) and node.get('enabled') == 'true'
                                        for node in tree.iter('node'))}
            return ('invitation', form) if form is not None else None
        kind, field = self.until(enrollment_input, 120)
        if kind == 'invitation':
            # An OS link may arrive without preserving its value. Exercise the
            # real form, and never report this fallback as OS-link qualification.
            require(re.fullmatch(r'gcoms://join#GCIR1-[A-Za-z0-9_-]+', invitation)
                    and len(invitation.encode()) <= 2048, 'bounded compact form invitation required')
            self.ui_observation['invitation_entry'] = 'os_link_with_visible_form'
            if field.get('text') != invitation:
                self.type(field, invitation)
            self.click('Continue')
            self.scroll_to_top()
            field = self.until(lambda: (node,) if (node := invitation_nickname(self.tree())) is not None else None, 120)[0]
        else:
            self.ui_observation['invitation_entry'] = 'os_link'
        self.type(field, 'MOBILE')
        self.click('Join')
        # A new network joins asynchronously and presents its saved enrollment
        # in a modal. Its Joined state does not select the conversation.
        def admitted():
            tree = self.tree()
            if any(self.text('Message or command')(node) for node in tree.iter('node')):
                return 'selected'
            if any(self.text('Joined')(node) for node in tree.iter('node')):
                return 'joined'
            return None
        state = self.until(admitted, 120)
        self.ui_observation['join_state'] = state
        if state == 'joined':
            self.click('Close dialog')
            self.click('Channels')
            self.tap(self.node(owned_channel))
        def ready():
            tree = self.tree()
            if any(self.text('Notifications')(node) for node in tree.iter('node')) and any(
                    self.text('Close dialog')(node) for node in tree.iter('node')):
                self.click('Close dialog')
                self.ui_observation['notification_dialog_dismissed'] = True
                return False
            self.ui_observation['editable_fields'] = sum(node.get('class') == 'android.widget.EditText'
                and node.get('password') != 'true' for node in tree.iter('node')
                if node.get('package') == android.PACKAGE)
            return editable_composer(tree) is not None
        self.until(ready, 120)

    def identity(self):
        tree = self.tree()
        if any(self.text('Notifications')(node) for node in tree.iter('node')) and any(
                self.text('Close dialog')(node) for node in tree.iter('node')):
            self.click('Close dialog')
        self.tap(self.node(lambda node: named_control(node, 'Network:')))
        self.click('Your identity')
        def identify():
            values = labels(self.tree())
            ids = {value for value in values if re.fullmatch('[0-9a-f]{64}', value)}
            safety = {value for value in values if re.fullmatch(r'[A-Z2-7]{8}(?: [A-Z2-7]{8}){4}', value)}
            return next(iter(ids)) + '\n' + next(iter(safety)) if len(ids) == len(safety) == 1 else None
        value = self.until(identify)
        self.click('Close dialog')
        return hashlib.sha256(value.encode()).hexdigest()

    def prepare_transcript(self):
        # The existing Readable font setting avoids Fixedsys glyph ambiguity
        # in ordinary screenshots. Select it through the normal command/UI.
        field = self.until(lambda: (node,) if (node := editable_composer(self.tree())) is not None else None)[0]
        self.type(field, '/font')
        self.click('Send')
        self.tap(self.node(lambda node: node.get('package') == android.PACKAGE
            and (self.text('Readable')(node) or named_control(node, 'Readable '))))
        self.click('Close dialog')
        self.until(lambda: editable_composer(self.tree()) is not None)
        self.ui_observation['transcript_font'] = 'readable'

    def send(self, body):
        self.bodies.add(body)
        field = self.until(lambda: (node,) if (node := editable_composer(self.tree())) is not None else None)[0]
        self.type(field, body)
        self.click('Send')

    def rendered_lines(self, tree):
        transcript = next((node for node in tree.iter('node') if node.get('package') == android.PACKAGE
            and any(node.get(key, '').endswith(' messages') for key in ('text', 'content-desc'))
            and android.ui_bounds(node)), None)
        if transcript is None: return []
        # Pixels and OCR text stay in memory; neither is written or uploaded.
        pixels = self.command('exec-out', 'screencap', '-p', binary=True)
        left = min(20, self.deadline()-time.monotonic())
        require(left > 0, 'original mobile journey deadline')
        attempts = self.ui_observation.get('pixel_observations', 0)
        mode = 11 if attempts % 2 == 0 else 6
        self.ui_observation.update(pixel_observations=attempts+1, pixel_segmentation_mode=mode)
        result = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(mode), 'tsv'],
            input=pixels, capture_output=True, timeout=left, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
        require(result.returncode == 0, 'owned Android pixel observation failed')
        self.ui_observation['pixel_observer_used'] = True
        controls = [android.ui_bounds(node) for node in tree.iter('node')
            if node.get('package') == android.PACKAGE and node.get('class') == 'android.widget.Button'
            and android.ui_bounds(node)]
        bounds = android.ui_bounds(transcript)
        controls = [box for box in controls if box[0] < bounds[2] and box[2] > bounds[0]
                    and box[1] < bounds[3] and box[3] > bounds[1]]
        self.ui_observation['pixel_overlay_controls'] = len(controls)
        lines = pixel_lines(result.stdout.decode(), bounds, controls)
        self.ui_observation['pixel_lines_count'] = len(lines)
        self.ui_observation['pixel_canary_prefix_lines'] = sum('Canary ' in line['text'] or 'mr-' in line['text'] for line in lines)
        return lines

    def received(self, body):
        self.bodies.add(body)
        tree = self.tree()
        nodes = [node for node in tree.iter('node') if node.get('package') == android.PACKAGE]
        values = [node.get(key, '') for node in nodes for key in ('text', 'content-desc')]
        transcript = next((node for node in nodes if any(node.get(key, '').endswith(' messages')
            for key in ('text', 'content-desc'))), None)
        all_values = labels(tree)
        self.ui_observation['receive_view'] = {
            'owned_channel_title': any(value == '#mobile-release' for value in values),
            'transcript_present': transcript is not None,
            'transcript_bounds': android.ui_bounds(transcript) if transcript is not None else None,
            'transcript_nodes': sum(1 for _ in transcript.iter('node')) if transcript is not None else 0,
            'beginning_visible': '*** Beginning of this conversation' in values,
            'loading_visible': 'Loading…' in values,
            'body_token_any_package': body in message_bodies(all_values, {body}),
            'body_after_whitespace_removal': any(body in re.sub(r'\s+', '', value) for value in values),
            'body_hex_visible': any(body[3:] in value for value in values),
            'canary_prefix_labels': sum('Canary ' in value or 'mr-' in value for value in values)}
        if body in message_bodies(values, {body}): return True
        return next(pixel_message_spans(self.rendered_lines(tree), body), None) is not None

    def delivered(self, body):
        tree = self.tree()
        if delivery_row(tree, body, self.bodies): return True
        lines = self.rendered_lines(tree)
        spans = list(pixel_message_spans(lines, body))
        self.ui_observation['pixel_delivery'] = {
            'complete_body_spans': len(spans),
            'body_word_layout': pixel_body_layout(lines, body),
            'exact_body_in_all_rows': bool(message_bodies([' '.join(line['text'] for line in lines)], {body})),
            'body_words_expected': len(body.split()),
            'body_words_observed': sum(any(re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)', line['text'])
                for line in lines) for word in body.split()),
            'delivered_lines': sum(bool(re.search(r'\bdelivered\b', line['text'])) for line in lines),
            'service_accepted_lines': sum('stored by service' in line['text'] for line in lines),
            'locally_accepted_lines': sum('accepted locally' in line['text'] for line in lines)}
        return pixel_delivered(lines, body, self.bodies)

    def history(self, bodies):
        self.bodies.update(bodies)
        missing = set(bodies)
        scrolled = 0
        # UIAutomator can omit offscreen WebView text. Walk the rendered
        # transcript, never a database or application instrumentation endpoint.
        for _ in range(12):
            tree = self.tree()
            missing.difference_update(message_bodies(labels(tree), missing))
            if missing:
                lines = self.rendered_lines(tree)
                missing.difference_update(body for body in list(missing)
                    if next(pixel_message_spans(lines, body), None) is not None)
            if not missing:
                break
            transcript = next((node for node in tree.iter('node')
                if any(node.get(key, '').endswith(' messages') for key in ('text','content-desc')) and android.ui_bounds(node)), None)
            require(transcript is not None, 'rendered mobile transcript unavailable')
            x1, y1, x2, y2 = android.ui_bounds(transcript)
            self.shell('input', 'swipe', (x1 + x2) // 2, y1 + (y2 - y1) // 4,
                       (x1 + x2) // 2, y1 + 3 * (y2 - y1) // 4, 250)
            scrolled += 1
        require(not missing, 'rendered mobile history was lost after replacement')
        # Return to the tail through the same transcript before sending again.
        for _ in range(scrolled):
            tree = self.tree()
            transcript = next((node for node in tree.iter('node')
                if any(node.get(key, '').endswith(' messages') for key in ('text','content-desc')) and android.ui_bounds(node)), None)
            if transcript is None:
                break
            x1, y1, x2, y2 = android.ui_bounds(transcript)
            self.shell('input', 'swipe', (x1 + x2) // 2, y1 + 3 * (y2 - y1) // 4,
                       (x1 + x2) // 2, y1 + (y2 - y1) // 4, 250)

    def file_action(self, name, action):
        self.names.add(name)
        self.tap(self.node(lambda node: named_control(node, 'Files:')))
        def find():
            for node in reversed(list(self.tree().iter('node'))):
                values = labels(node)
                if name in values and set(values) & self.names == {name}:
                    button = next((child for child in node.iter('node')
                                   if self.text(action)(child) and android.ui_bounds(child)), None)
                    if button is not None:
                        return (button,)
            return None
        self.tap(self.until(find, 120)[0])
        if action != 'Save file…':
            self.click('Close dialog')

    def progress(self, name, size):
        self.names.add(name)
        tree = self.tree()
        for node in tree.iter('node'):
            values = labels(node)
            if name in values and set(values) & self.names == {name}:
                for value in values:
                    match = re.fullmatch(r'([\d,]+) / ([\d,]+) bytes verified', value)
                    if match and int(match[2].replace(',', '')) == size:
                        return int(match[1].replace(',', ''))
        observed = pixel_transfer_progress(self.rendered_lines(tree), name, size, self.names)
        if observed is not None:
            return observed
        # Completed transfer rows are transient. On reopen, the retained Files
        # pane still reports the exact file's verified completion state.
        self.tap(self.node(lambda node: named_control(node, 'Files:')))
        complete = completed_file_row(self.tree(), name, self.names)
        self.click('Close dialog')
        return size if complete else None

    def cache_hash(self, ident):
        require(re.fullmatch('[0-9a-f]{32}', ident), 'invalid retained file ID')
        # Tauri's Android app_data_dir is activity.dataDir, not filesDir.
        # Both retained apps create their private instance directly below it.
        root = '/data/user/0/' + android.PACKAGE + '/instance'
        paths = self.shell('find', root, '-type', 'f', '-name', '*.piece').splitlines()
        selected = [path for path in paths if Path(path).parent.name == ident]
        require(len(selected) == 1 and Path(selected[0]).name == '0.piece'
                and selected[0].startswith(root + '/'), 'one retained encrypted cache piece required')
        return hashlib.sha256(self.command('exec-out', 'cat', selected[0], binary=True)).hexdigest()

    def export(self, name, phase, expected_sha256=None):
        self.file_action(name, 'Save file…')
        filename = 'gchat-acceptance-' + phase + '.bin'
        require(re.fullmatch(r'gchat-acceptance-[a-z0-9-]+\.bin', filename), 'invalid owned export name')
        field = self.node(lambda node: node.get('package', '').endswith('.documentsui')
                          and node.get('class') == 'android.widget.EditText', 30)
        self.type(field, filename, system_export=True, replace=True)
        # Select the system provider's Downloads root and save its exact bytes.
        root = self.node(lambda node: system_picker_control(node, ('Downloads', 'Show roots')), 30)
        if system_picker_control(root, ('Show roots',)):
            self.tap(root)
            root = self.node(lambda node: system_picker_control(node, ('Downloads',)), 15)
        self.tap(root)
        self.tap(self.node(lambda node: system_picker_control(node, ('Save', 'SAVE')), 30))
        path = '/sdcard/Download/' + filename
        self.exports.append(path)
        self.until(lambda: filename in self.shell('ls', '-1', '/sdcard/Download').splitlines(), 30)
        if expected_sha256 is not None:
            require(re.fullmatch('[0-9a-f]{64}', expected_sha256), 'expected export hash required')
        def complete():
            data = self.command('exec-out', 'cat', path, binary=True)
            actual = hashlib.sha256(data).hexdigest()
            self.ui_observation['export_copy'] = {'bytes':len(data), 'hash_matched':actual == expected_sha256}
            return actual if expected_sha256 is None or actual == expected_sha256 else None
        return self.until(complete, 30)

    def resume_after_export(self):
        # Reconnect through normal UI when the next operation requires it.
        # A replacement immediately after export needs only its own unlock.
        self.unlock()

    def cleanup(self):
        errors = []
        if self.installed:
            for operation in (lambda: self.stop(), lambda: self.command('uninstall', android.PACKAGE)):
                try:
                    operation()
                except Exception as error:
                    errors.append(type(error).__name__)
        try:
            self.shell('rm', '-f', self.dump, *self.exports)
            require(not self.shell('pm', 'path', android.PACKAGE, absent=True),
                    'owned mobile profile was not removed')
        except Exception as error:
            errors.append(type(error).__name__)
        return {'passed': not errors, 'errors': errors}
