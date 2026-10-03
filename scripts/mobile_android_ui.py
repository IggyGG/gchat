"""Real accessibility/picker driver for a newly created, owned Android AVD.

UI hierarchies and invitation values stay in memory. No application endpoint,
debug build, WebView instrumentation or personal-device operation is used.
"""
import hashlib
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


def delivery_row(tree, body, known_bodies):
    # A delivered suffix elsewhere in the transcript cannot qualify this send.
    # Require one smallest message subtree containing exactly this test body.
    for node in reversed(list(tree.iter('node'))):
        values = labels(node)
        if body in values and any(value.strip() == '· delivered' for value in values):
            if {value for value in values if value in known_bodies} == {body}:
                return True
    return False


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
        self.shell('rm', '-f', self.dump)
        try:
            self.shell('uiautomator', 'dump', self.dump)
            tree = ET.fromstring(self.shell('cat', self.dump))
        except (ValueError, ET.ParseError) as error:
            self.ui_observation.update(errors=self.ui_observation['errors']+1, last_error=type(error).__name__)
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

    def type(self, node, value):
        self.ui_observation['input_target_bounds'] = android.ui_bounds(node)
        self.tap(node)
        # WebView focus and the IME arrive asynchronously. Pressing Back before
        # the keyboard appears closes the app instead of dismissing the IME.
        android.wait_keyboard(self.shell, True)
        self.input_started = True
        self.shell('input', 'text', shlex.quote(value.replace(' ', '%s')))
        self.until(lambda: any(child.get('focused') == 'true' and child.get('text') == value
                              for child in self.tree().iter('node')), 10)
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
        self.until(lambda: not any(self.text(button)(node) for node in self.tree().iter('node')), 120)
        self.no_listener()

    def join(self, invitation):
        require(invitation.startswith('gcoms:') and len(invitation.encode()) <= 180000,
                'bounded conversation invitation required')
        self.shell('am', 'start', '-W', '-a', 'android.intent.action.VIEW',
                   '-d', shlex.quote(invitation), android.PACKAGE)
        self.click('Review invitation')
        self.scroll_to_top()
        field = self.until(lambda: (node,) if (node := invitation_nickname(self.tree())) is not None else None, 120)[0]
        self.type(field, 'mobile')
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

    def send(self, body):
        self.bodies.add(body)
        field = self.until(lambda: (node,) if (node := editable_composer(self.tree())) is not None else None)[0]
        self.type(field, body)
        self.click('Send')

    def received(self, body):
        self.bodies.add(body)
        return body in labels(self.tree())

    def delivered(self, body):
        return delivery_row(self.tree(), body, self.bodies)

    def history(self, bodies):
        self.bodies.update(bodies)
        missing = set(bodies)
        scrolled = 0
        # UIAutomator can omit offscreen WebView text. Walk the rendered
        # transcript, never a database or application instrumentation endpoint.
        for _ in range(12):
            tree = self.tree()
            missing.difference_update(labels(tree))
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
        for node in self.tree().iter('node'):
            values = labels(node)
            if name in values and set(values) & self.names == {name}:
                for value in values:
                    match = re.fullmatch(r'([\d,]+) / ([\d,]+) bytes verified', value)
                    if match and int(match[2].replace(',', '')) == size:
                        return int(match[1].replace(',', ''))
        # Completed transfer rows are transient. On reopen, the retained Files
        # pane still reports the exact file's verified completion state.
        self.tap(self.node(lambda node: named_control(node, 'Files:')))
        complete = completed_file_row(self.tree(), name, self.names)
        self.click('Close dialog')
        return size if complete else None

    def cache_hash(self, ident):
        require(re.fullmatch('[0-9a-f]{32}', ident), 'invalid retained file ID')
        root = '/data/user/0/' + android.PACKAGE + '/files'
        paths = self.shell('find', root, '-type', 'f', '-name', '*.piece').splitlines()
        selected = [path for path in paths if Path(path).parent.name == ident]
        require(len(selected) == 1 and Path(selected[0]).name == '0.piece'
                and selected[0].startswith(root + '/'), 'one retained encrypted cache piece required')
        return hashlib.sha256(self.command('exec-out', 'cat', selected[0], binary=True)).hexdigest()

    def export(self, name, phase):
        self.file_action(name, 'Save file…')
        filename = 'gchat-acceptance-' + phase + '.bin'
        require(re.fullmatch(r'gchat-acceptance-[a-z0-9-]+\.bin', filename), 'invalid owned export name')
        field = self.node(lambda node: node.get('package', '').endswith('.documentsui')
                          and node.get('class') == 'android.widget.EditText', 30)
        self.tap(field)
        self.shell('input', 'keyevent', 'KEYCODE_MOVE_END')
        require(0 < len(field.get('text', '')) <= 255, 'unexpected system export filename')
        self.shell('input', 'keyevent', *(['KEYCODE_DEL'] * len(field.get('text', ''))))
        self.type(field, filename)
        self.node(lambda node: node.get('package', '').endswith('.documentsui')
                  and node.get('class') == 'android.widget.EditText' and node.get('text') == filename, 10)
        # Select the system provider's Downloads root and save its exact bytes.
        self.tap(self.node(lambda node: node.get('package', '').endswith('.documentsui')
                          and node.get('content-desc') == 'Show roots', 30))
        self.click('Downloads')
        self.click('Save')
        path = '/sdcard/Download/' + filename
        self.exports.append(path)
        self.until(lambda: filename in self.shell('ls', '-1', '/sdcard/Download').splitlines(), 30)
        data = self.command('exec-out', 'cat', path, binary=True)
        # Returning from the real system picker preserves the manual unlock flow.
        self.unlock()
        return hashlib.sha256(data).hexdigest()

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
