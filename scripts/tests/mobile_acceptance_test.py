import copy
import os
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mobile_acceptance_inputs as inputs
from mobile_android_ui import delivery_row
from mobile_ios_ui import Bridge, IOSUI, owned_simulator_binding, runner_diagnostics
from mobile_installed_journey import MobileJourney
import release_acceptance as acceptance
import mobile_android_ui as android_ui
from release_acceptance_test import fixture
from release_automation_test import candidate
from release_pair import canonical
from release_network_canary import module


def mobile_fixture(target='android'):
    manifest, specs, report, rollback, network = fixture()
    specs.update(target=target, peer_target='linux-x86_64' if target == 'android' else 'macos-aarch64',
                 peer=copy.deepcopy(specs['current']))
    report.update(platform=target, application_resigned=False, ui_driven=True,
                  physical_device_qualified=False, installation_cleanup=[{'passed': True}])
    for phase in rollback['phases']:
        phase['encrypted_cache_sha256'] = '9' * 64
    return manifest, specs, report, rollback, network


class MobileAcceptanceTests(unittest.TestCase):
    def test_verified_retained_ios_handoff_preserves_original_failure_and_checks_all_gate_bytes(self):
        import release_ios_recovery as recovery
        from release_macos_recovery import REGISTRY
        from release_ios_recovery_test import IosRecoveryTests
        case=IosRecoveryTests(); case.setUp()
        manifest=candidate(); manifest['policy']['ios_certificate_sha256']='a'*64
        manifest['release_id']=hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
        config=copy.deepcopy(next(v for v in json.loads(REGISTRY.read_text())['recoveries'] if v['kind']=='ios-retained'))
        config.update(release_id=manifest['release_id'],sources=manifest['sources'])
        reviewed={**recovery.INPUTS, 'run_id':config['original_run'],'artifact_id':config['original_artifact'],
                  'artifact_sha256':config['original_sha256'],'build_number':manifest['versions']['ios'],
                  **{p+'_commit':manifest['sources'][p]['commit'] for p in ('gchat','gcoms')},
                  'simulator':{'mode':'retained_original','run_id':config['lifecycle']['run'],
                               'controller_commit':config['lifecycle']['controller'],
                               'request_id':config['lifecycle']['request']}}
        rule={'release_id':manifest['release_id'],'run':123,'artifact':456,'controller':config['verification']['controller'],
              'request':config['verification']['request'],'original_run':config['original_run'],
              'ipa':config['ipa'],'inputs':reviewed,'registration':config}
        report=copy.deepcopy(case.report)
        report.update(sources=manifest['sources'],inputs=reviewed)
        report['application'].update(ipa={'sha256':config['ipa']},build_number=manifest['versions']['ios'],
                                     marketing_version=manifest['versions']['linux-x86_64'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); registry=root/'registry.json'
            registry.write_text(json.dumps({'schema':1,'recoveries':[config]}))
            files={'ios-verification/original/ios-output/build.json':canonical({'passed':False,'sources':manifest['sources']})}
            def reference(name,value):
                path='ios-verification/'+name; data=canonical(value); files[path]=data
                return {'path':'/native/'+path,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
            original=files['ios-verification/original/ios-output/build.json']
            report['original_build']={'path':'/native/ios-verification/original/ios-output/build.json',
                                      'sha256':hashlib.sha256(original).hexdigest(),'size':len(original)}
            report['signing_cleanup']=reference('cleanup.json',{'passed':True})
            report['simulator']=reference('lifecycle.json',{'passed':True})
            report['simulator_binding']={'verification':reference('linked.json',{'passed':True})}
            import io
            import zipfile
            nested=io.BytesIO()
            with zipfile.ZipFile(nested,'w') as bundle:
                bundle.writestr('ios-output/build.json',original)
                bundle.writestr('ios-output/simulator-app.zip',b'original simulator archive')
            files['ios-verification/original-artifact.zip']=nested.getvalue()
            reviewed['artifact_sha256']=hashlib.sha256(nested.getvalue()).hexdigest()
            config['original_sha256']=reviewed['artifact_sha256']
            registry.write_text(json.dumps({'schema':1,'recoveries':[config]}))
            files['ios-verification/build.json']=canonical(report)
            archive=root/'provider.zip'
            with zipfile.ZipFile(archive,'w') as bundle:
                for name,data in files.items(): bundle.writestr(name,data)
            rule.update(sha256=inputs.digest(archive),size=archive.stat().st_size)
            run={'id':rule['run'],'head_sha':rule['controller'],'path':'.github/workflows/ios-verify.yml',
                 'head_repository':{'full_name':'IggyGG/gchat'},'display_title':'iOS retained verification '+rule['request'],
                 'event':'workflow_dispatch','status':'completed','conclusion':'success'}
            artifact={'id':rule['artifact'],'expired':False,'workflow_run':{'id':rule['run']},
                      'digest':'sha256:'+rule['sha256'],'size_in_bytes':rule['size'],'name':'ios-verified-'+rule['request']}
            spec={'run':rule['run'],'artifact':rule['artifact'],'archive':rule['sha256'],'controller':rule['controller'],
                  'sources':{p:v['commit'] for p,v in manifest['sources'].items()},'manifest':'ios-verification/build.json',
                  'conclusion':'success','recovery':{'kind':'ios-retained','candidate':manifest,'rule':rule,'inputs':reviewed}}
            from release_acceptance_delivery import provider_metadata
            artifact=provider_metadata(archive,spec,'ios')
            self.assertNotIn('expired',artifact)
            with self.assertRaisesRegex(ValueError,'archive differs'):
                recovery.validate_run(manifest,run,artifact,rule)
            recovery.validate_run(manifest,run,artifact,rule,retained=True)
            with self.assertRaisesRegex(ValueError,'archive differs'):
                recovery.validate_run(manifest,run,{**artifact,'retained_locally':False},rule,retained=True)
            def retained(bound,destination): destination.write_bytes(archive.read_bytes()); return artifact
            with patch.dict(os.environ,{'GCHAT_NATIVE_RECOVERIES':str(registry)}), \
                 patch.object(inputs,'gh',return_value=run),patch.object(inputs,'acceptance_archive',side_effect=retained):
                item=inputs.acquire('current',spec,'ios',root,manifest)
                self.assertIs(item['build']['passed'],False)
                self.assertTrue(json.loads(item['retained_lifecycle'].read_text())['passed'])
                self.assertEqual((item['root']/'simulator-app.zip').read_bytes(),b'original simulator archive')
                verification_root=item['retained_lifecycle'].parent
                item['retained_lifecycle'].write_text('{"passed":false}')
                with self.assertRaisesRegex(ValueError,'reference changed'):
                    recovery.reference(report['simulator'],verification_root)
                for invalid in ('workflow','request','candidate','registration'):
                    with self.subTest(invalid=invalid):
                        changed_run=copy.deepcopy(run); changed=copy.deepcopy(spec)
                        if invalid=='workflow': changed_run['path']='.github/workflows/ios-release.yml'
                        if invalid=='request': changed_run['display_title']='another request'
                        if invalid=='candidate': changed['recovery']['candidate']=candidate(2)
                        if invalid=='registration': changed['recovery']['rule']['registration']['ipa']='0'*64
                        with patch.object(inputs,'gh',return_value=changed_run),self.assertRaises(ValueError):
                            inputs.acquire(invalid,changed,'ios',root,manifest)

    def owned_android_ui(self, root, *, sdk_setup=False, qemu=True, avd=True, installed=False):
        def command(argv, **kwargs):
            args = tuple(argv[3:])
            result, code = '', 0
            if args == ('shell', 'getprop', 'ro.kernel.qemu'): result = '1' if qemu else '0'
            elif args == ('emu', 'avd', 'name'): result = 'gchat-release-fixture-5554\nOK' if avd else 'another-owned-avd\nOK'
            elif args[:3] == ('shell', 'pm', 'path'):
                present = installed if args[3] == android_ui.android.PACKAGE else sdk_setup
                result, code = ('package:/fixture.apk', 0) if present else ('', 1)
            elif args[:3] == ('shell', 'pm', 'disable-user'): result = 'disabled-user'
            elif args[:2] == ('shell', 'settings') and 'get' in args: result = '1'
            elif args == ('shell', 'locksettings', 'get-disabled'): result = 'true'
            elif args == ('shell', 'getprop', 'ro.product.cpu.abi'): result = 'x86_64'
            elif args == ('shell', 'getprop', 'ro.build.version.sdk'): result = '35'
            return SimpleNamespace(returncode=code, stdout=result.encode(), stderr=b'')
        with patch.object(android_ui.android, 'sdk', return_value=root), \
             patch.object(android_ui.android, 'root_emulator') as rooted, \
             patch.object(android_ui.subprocess, 'run', side_effect=command) as adb:
            ui = android_ui.AndroidUI('emulator-5554', root, 'fixture-private-value', lambda: time.monotonic()+60)
        return ui, rooted, adb

    def test_mobile_android_ui_runs_shared_disposable_setup_with_absent_optional_package(self):
        for installed in (False, True):
            with self.subTest(sdk_setup=installed), tempfile.TemporaryDirectory() as temporary:
                ui, rooted, adb = self.owned_android_ui(Path(temporary), sdk_setup=installed)
                self.assertFalse(ui.installed)
                rooted.assert_called_once()
                calls = [call.args[0][3:] for call in adb.call_args_list]
                self.assertIn(['shell', 'pm', 'path', 'com.google.android.googlesdksetup'], calls)
                self.assertIn(['shell', 'locksettings', 'get-disabled'], calls)
                self.assertEqual(any('disable-user' in argv for argv in calls), installed)

    def test_mobile_setup_still_refuses_physical_other_or_preinstalled_device(self):
        for options in ({'qemu': False}, {'avd': False}, {'installed': True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
                self.owned_android_ui(Path(temporary), **options)

    def test_android_accessibility_reveals_existing_offscreen_controls_before_original_deadline(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            hidden=ET.fromstring('<hierarchy><node package="boo.gchat.app" bounds="[0,0][100,200]">'
                '<node text="Create identity" bounds="[0,0][0,0]"/></node></hierarchy>')
            visible=ET.fromstring('<hierarchy><node package="boo.gchat.app" bounds="[0,0][100,200]">'
                '<node text="Create identity" bounds="[10,10][90,40]"/></node></hierarchy>')
            with patch.object(ui,'tree',side_effect=[hidden,visible]),patch.object(ui,'shell') as shell, \
                 patch.object(android_ui.time,'sleep'):
                node=ui.node(ui.text('Create identity'))
            self.assertEqual(node.get('text'),'Create identity')
            shell.assert_called_once_with('input','swipe',50,160,50,66,'250')

    def test_mobile_failure_locations_exclude_exception_messages_and_private_paths(self):
        driver = module('test-mobile-upgrade')
        try:
            raise TypeError('private-test-invitation /private/profile/path')
        except TypeError as error:
            frames = driver.error_frames(error)
        self.assertTrue(frames)
        self.assertEqual(set(frames[0]), {'file','function','line'})
        self.assertEqual(frames[0]['file'], Path(__file__).name)
        encoded = json.dumps(frames)
        self.assertNotIn('private-test-invitation', encoded)
        self.assertNotIn('/private/profile/path', encoded)

    def test_android_startup_diagnostics_retain_control_counts_without_private_hierarchy(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            xml='<hierarchy><node package="boo.gchat.app" text="private-canary-invitation">' \
                '<node package="boo.gchat.app" text="Create identity"/>' \
                '<node package="boo.gchat.app" password="true" text="private-passphrase"/>' \
                '</node></hierarchy>'
            with patch.object(ui,'shell',side_effect=['','',xml]):
                self.assertEqual(len(list(ui.tree().iter('node'))),3)
            self.assertEqual(ui.ui_observation,{'attempts':1,'errors':0,'application_nodes':3,
                'display_size':[720,1440],'display_density':360,
                'password_fields':1,'create_identity':1,'reconnect':0,
                'public_controls':{'network':0,'files':0,'send':0,'connect_to_gchat':0,'close_dialog':0,'close_details':0,'nickname':0,'invitation_preview':0,'join':0,
                    'continue':0,'validating':0,'notifications':0}})
            with patch.object(ui,'shell',side_effect=['','', 'invalid private hierarchy']):
                self.assertEqual(ui.tree().tag,'hierarchy')
            self.assertEqual(ui.ui_observation['last_error'],'ParseError')
            self.assertEqual(ui.ui_observation['errors'],1)
            self.assertNotIn('private',json.dumps(ui.ui_observation))

    def test_android_startup_capture_is_limited_to_the_fresh_owned_screen_before_any_input(self):
        for create,typed,field in ((True,False,False),(True,False,True),(True,True,True),(False,False,True)):
            with self.subTest(create=create,typed=typed,field=field),tempfile.TemporaryDirectory() as temporary:
                ui,_,_=self.owned_android_ui(Path(temporary));ui.input_started=typed
                observations=[ET.Element('node'),TimeoutError] if field else [TimeoutError]
                with patch.object(ui,'launch'),patch.object(ui,'scroll_to_top'),patch.object(ui,'node',side_effect=observations), \
                     patch.object(ui,'shell',return_value='fixture-process'), \
                     patch.object(android_ui.android,'screenshot') as screenshot, \
                     self.assertRaises(TimeoutError):
                    ui.unlock(create=create)
                self.assertEqual(screenshot.call_count,int(create and not typed))
                self.assertNotIn('fixture-private-value',json.dumps(ui.ui_observation))

    def test_android_unlock_returns_from_submit_to_password_fields_before_entering_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));events=[]
            def node(predicate,*args):
                events.append('find-control')
                return ET.Element('node')
            with patch.object(ui,'launch'),patch.object(ui,'node',side_effect=node), \
                 patch.object(ui,'scroll_to_top',side_effect=lambda:events.append('reveal-fields')), \
                 patch.object(ui,'type',side_effect=lambda *args:events.append('enter-text')), \
                 patch.object(ui,'click'),patch.object(ui,'until'),patch.object(ui,'no_listener'):
                ui.unlock(create=True)
            self.assertEqual(events,['find-control','reveal-fields','find-control','enter-text','find-control','enter-text'])

    def test_android_input_waits_for_keyboard_and_exact_focused_value_before_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));events=[]
            node=ET.Element('node',{'package':'boo.gchat.app','class':'android.widget.EditText',
                'focused':'true','text':'fixture-private-value'})
            with patch.object(ui,'tap',side_effect=lambda n:events.append('tap')), \
                 patch.object(android_ui.android,'wait_keyboard',side_effect=lambda shell,up:events.append('keyboard-up' if up else 'keyboard-down')), \
                 patch.object(ui,'shell',side_effect=lambda *args:events.append(args[:2])), \
                 patch.object(ui,'tree',side_effect=lambda:events.append('observed-input') or node):
                ui.type(node,'fixture-private-value')
            self.assertEqual(events,['tap','keyboard-up','observed-input',('input','text'),'observed-input',('input','keyevent'),'keyboard-down'])
            self.assertEqual(ui.ui_observation['inputs_confirmed'],1)
            self.assertNotIn('fixture-private-value',json.dumps(ui.ui_observation))

    def test_android_missing_keyboard_never_types_or_sends_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            with patch.object(ui,'tap'),patch.object(android_ui.android,'wait_keyboard',side_effect=ValueError), \
                 patch.object(ui,'shell') as shell,self.assertRaises(ValueError):
                ui.type(ET.Element('node',{'package':'boo.gchat.app'}),'fixture-private-value')
            shell.assert_not_called()
            self.assertNotIn('inputs_confirmed',ui.ui_observation)
            self.assertFalse(ui.input_started)

    def test_android_system_export_requires_explicit_picker_and_exact_focused_filename(self):
        for package in ('com.android.documentsui','com.google.android.documentsui','another.documentsui'):
            with self.subTest(package=package),tempfile.TemporaryDirectory() as temporary:
                ui,_,_=self.owned_android_ui(Path(temporary))
                field=ET.Element('node',{'package':package,'class':'android.widget.EditText',
                    'resource-id':'filename','focused':'true','text':'gchat-acceptance-initial.bin'})
                with patch.object(ui,'tap'),patch.object(android_ui.android,'wait_keyboard'), \
                     patch.object(ui,'tree',return_value=field),patch.object(ui,'shell') as shell:
                    with self.assertRaisesRegex(ValueError,'system export picker'):
                        ui.type(field,'gchat-acceptance-initial.bin')
                    shell.assert_not_called()
                    if package=='another.documentsui':
                        with self.assertRaisesRegex(ValueError,'system export picker'):
                            ui.type(field,'gchat-acceptance-initial.bin',system_export=True)
                        shell.assert_not_called()
                    else:
                        ui.type(field,'gchat-acceptance-initial.bin',system_export=True)
                        self.assertEqual(ui.ui_observation['inputs_confirmed'],1)
                        field.set('text','gchat-acceptance-modified.bin')
                        def check(fn,*args):
                            if not fn():raise TimeoutError('exact filename observation')
                            return True
                        with patch.object(ui,'until',side_effect=check),self.assertRaises(TimeoutError):
                            ui.type(field,'gchat-acceptance-initial.bin',system_export=True)
                        self.assertEqual(ui.ui_observation['inputs_confirmed'],1)

    def test_android_keyboard_presence_does_not_replace_intended_field_focus(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            target=ET.Element('node',{'package':'boo.gchat.app','class':'android.widget.EditText',
                'resource-id':'nickname','content-desc':'Your nickname in this channel'})
            wrong=ET.Element('node',{'package':'another.app','class':'android.widget.EditText',
                'focused':'true','resource-id':'nickname','content-desc':'Your nickname in this channel'})
            def check(fn,*args):
                self.assertFalse(fn());raise TimeoutError('focus observation')
            with patch.object(ui,'tap'),patch.object(android_ui.android,'wait_keyboard'), \
                 patch.object(ui,'tree',return_value=wrong),patch.object(ui,'until',side_effect=check), \
                 patch.object(ui,'shell') as shell,self.assertRaises(TimeoutError):
                ui.type(target,'mobile')
            shell.assert_not_called();self.assertFalse(ui.input_started)

    def test_android_changed_case_diagnostic_does_not_accept_modified_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));calls=[]
            target=ET.Element('node',{'package':'boo.gchat.app','class':'android.widget.EditText',
                'resource-id':'nickname','focused':'true','text':'Mobile'})
            def check(fn,*args):
                calls.append(fn())
                if len(calls)==2:raise TimeoutError('exact input observation')
                return calls[-1]
            with patch.object(ui,'tap'),patch.object(android_ui.android,'wait_keyboard'), \
                 patch.object(ui,'tree',return_value=target),patch.object(ui,'until',side_effect=check), \
                 patch.object(ui,'shell') as shell,self.assertRaises(TimeoutError):
                ui.type(target,'mobile')
            self.assertEqual(calls,[True,False])
            self.assertEqual(ui.ui_observation['input_value']['case_changed_fields'],1)
            self.assertEqual(ui.ui_observation['input_value']['exact_value_fields'],0)
            self.assertNotIn('Mobile',json.dumps(ui.ui_observation))
            self.assertNotIn('inputs_confirmed',ui.ui_observation)
            self.assertFalse(any(call.args[:2]==('input','keyevent') for call in shell.call_args_list))

    def test_android_join_selects_the_channel_after_async_enrollment_modal(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));clicks=[]
            preview=ET.fromstring('<hierarchy><node text="Join #mobile-release on Canary"/><node text="Join"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/></hierarchy>')
            joined=ET.fromstring('<hierarchy><node text="Joined"/></hierarchy>')
            composer=ET.fromstring('<hierarchy><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,400][290,450]" content-desc="Message or command"/></hierarchy>')
            with patch.object(ui,'shell'),patch.object(ui,'node',return_value=ET.Element('node')), \
                 patch.object(ui,'type'),patch.object(ui,'click',side_effect=clicks.append), \
                 patch.object(ui,'tree',side_effect=[preview,joined,composer]),patch.object(ui,'scroll_to_top'),patch.object(ui,'tap') as tap:
                ui.join('gcoms://join#GCI1-fixture')
            self.assertEqual(clicks,['Review invitation','Join','Close dialog','Channels'])
            tap.assert_called_once()
            self.assertEqual(ui.ui_observation['join_state'],'joined')

    def test_join_dismisses_first_run_notifications_before_observing_the_composer(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));clicks=[]
            screens=[ET.fromstring(xml) for xml in (
                '<hierarchy><node text="Join #mobile-release on Canary"/><node text="Join"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/></hierarchy>',
                '<hierarchy><node text="Joined"/></hierarchy>',
                '<hierarchy><node text="Notifications"/><node content-desc="Close dialog"/></hierarchy>',
                '<hierarchy><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,400][290,450]" content-desc="Message or command"/></hierarchy>')]
            with patch.object(ui,'shell'),patch.object(ui,'node',return_value=ET.Element('node')), \
                 patch.object(ui,'type'),patch.object(ui,'click',side_effect=clicks.append), \
                 patch.object(ui,'tree',side_effect=screens),patch.object(ui,'scroll_to_top'),patch.object(ui,'tap'),patch.object(android_ui.time,'sleep'):
                ui.join('gcoms://join#GCI1-fixture')
            self.assertEqual(clicks,['Review invitation','Join','Close dialog','Channels','Close dialog'])
            self.assertTrue(ui.ui_observation['notification_dialog_dismissed'])

    def test_android_join_uses_visible_blank_form_without_qualifying_os_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));clicks=[];typed=[]
            screens=[ET.fromstring(xml) for xml in (
                '<hierarchy><node package="boo.gchat.app" text="Invitation"/><node package="boo.gchat.app" text="Continue"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/></hierarchy>',
                '<hierarchy><node text="Join #mobile-release on Canary"/><node text="Join"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/></hierarchy>',
                '<hierarchy><node text="Message or command"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,400][290,450]"/></hierarchy>',
                '<hierarchy><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,400][290,450]"/></hierarchy>')]
            invitation='gcoms://join#GCIR1-private_fixture'
            with patch.object(ui,'shell'),patch.object(ui,'type',side_effect=lambda n,v:typed.append(v)), \
                 patch.object(ui,'click',side_effect=clicks.append),patch.object(ui,'tree',side_effect=screens), \
                 patch.object(ui,'scroll_to_top'):
                ui.join(invitation)
            self.assertEqual(clicks,['Review invitation','Continue','Join'])
            self.assertEqual(typed,[invitation,'MOBILE'])
            self.assertEqual(ui.ui_observation['invitation_entry'],'os_link_with_visible_form')
            self.assertNotIn('private_fixture',json.dumps(ui.ui_observation))

    def test_android_invitation_form_requires_owned_blank_field_and_both_controls(self):
        controls='<node package="boo.gchat.app" text="Invitation"/><node package="boo.gchat.app" text="Continue"/>'
        field='<node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/>'
        self.assertIsNotNone(android_ui.invitation_form(ET.fromstring('<hierarchy>'+controls+field+'</hierarchy>')))
        self.assertIsNotNone(android_ui.invitation_form(ET.fromstring('<hierarchy>'+controls+
            field.replace('bounds=', 'text="Paste an invitation" bounds=')+'</hierarchy>')))
        for changed in (field,controls.replace('Invitation','Message')+field,
                        controls.replace('Continue','Send')+field, controls.replace('boo.gchat.app','another.app')+field,
                        controls+field.replace('bounds=', 'text="private-existing-input" bounds='),controls+field+field):
            with self.subTest(changed=changed):
                self.assertIsNone(android_ui.invitation_form(ET.fromstring('<hierarchy>'+changed+'</hierarchy>')))

    def test_android_populated_invitation_form_must_match_the_exact_reserved_link(self):
        invitation='gcoms://join#GCIR1-private-fixture'
        tree=ET.fromstring('<hierarchy><node package="boo.gchat.app" text="Invitation"/>'
            '<node package="boo.gchat.app" text="Continue"/><node package="boo.gchat.app" '
            'class="android.widget.EditText" text="'+invitation+'" bounds="[10,100][290,150]"/></hierarchy>')
        self.assertIsNotNone(android_ui.invitation_form(tree,invitation))
        self.assertIsNone(android_ui.invitation_form(tree,invitation+'-different'))
        self.assertIsNone(android_ui.invitation_form(tree))

    def test_ios_command_clipboard_is_cleared_after_success_or_ui_failure(self):
        for failed in (False,True):
            ui=IOSUI.__new__(IOSUI);ui.runner=SimpleNamespace(poll=lambda:None)
            ui.deadline=lambda:time.monotonic()+120
            from unittest.mock import Mock
            ui.bridge=SimpleNamespace(call=Mock(side_effect=ValueError if failed else None,return_value=True))
            with patch.object(ui,'copy_input') as copy:
                if failed:
                    with self.assertRaises(ValueError):ui.call('unlock',passphrase='private input')
                else:self.assertTrue(ui.call('unlock',passphrase='private input'))
            self.assertEqual([c.args[0] for c in copy.call_args_list],['private input',''])
            self.assertLessEqual(ui.bridge.call.call_args.kwargs['timeout'],120)

    def test_ios_clipboard_refuses_foreign_devices_changed_bytes_and_expired_deadlines(self):
        ui=IOSUI.__new__(IOSUI);ui.device='owned';ui.owned_devices={'owned'};ui.before_devices=set()
        with patch('mobile_ios_ui.subprocess.run') as run, \
             patch('mobile_ios_ui.subprocess.check_output',return_value=b'private input'):
            ui.copy_input('private input',time.monotonic()+10)
        self.assertEqual(run.call_args.args[0],['xcrun','simctl','pbcopy','owned'])
        self.assertNotIn('private input',' '.join(run.call_args.args[0]))
        self.assertEqual(run.call_args.kwargs['input'],b'private input')
        with patch('mobile_ios_ui.subprocess.run'), \
             patch('mobile_ios_ui.subprocess.check_output',return_value=b'changed'), \
             self.assertRaisesRegex(ValueError,'differs'):
            ui.copy_input('private input',time.monotonic()+10)
        for device,before,end in [('other',set(),time.monotonic()+10),
                                 ('owned',{'owned'},time.monotonic()+10),
                                 ('owned',set(),time.monotonic()-1)]:
            ui.device=device;ui.before_devices=before
            with patch('mobile_ios_ui.subprocess.run') as run,self.assertRaises(ValueError):
                ui.copy_input('private input',end)
            run.assert_not_called()

    def test_android_form_fallback_refuses_long_or_legacy_invitation(self):
        form=ET.fromstring('<hierarchy><node package="boo.gchat.app" text="Invitation"/><node package="boo.gchat.app" text="Continue"/><node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/></hierarchy>')
        for invitation in ('gcoms://join#GCI1-private_fixture','gcoms://join#GCIR1-'+'x'*2048):
            with self.subTest(size=len(invitation)),tempfile.TemporaryDirectory() as temporary:
                ui,_,_=self.owned_android_ui(Path(temporary))
                with patch.object(ui,'shell'),patch.object(ui,'click'),patch.object(ui,'scroll_to_top'), \
                     patch.object(ui,'tree',return_value=form),patch.object(ui,'type') as typed, \
                     self.assertRaisesRegex(ValueError,'bounded compact'):
                    ui.join(invitation)
                typed.assert_not_called()

    def test_ios_startup_pixels_require_first_creation_and_failure_before_any_input(self):
        for create,attempted,phase in ((True,False,'unlock-start'),(True,True,'unlock-start'),
                                      (False,False,'unlock-start'),(True,False,'unlock-passphrase')):
            with self.subTest(create=create,attempted=attempted,phase=phase),tempfile.TemporaryDirectory() as temporary:
                ui=IOSUI.__new__(IOSUI);ui.output=Path(temporary)/'owned';ui.device='owned-device'
                ui.passphrase='private-test-value';ui.unlock_attempted=attempted
                error=ValueError('public failure');error.ios_observation_phase=phase
                with patch.object(ui,'call',side_effect=error),patch('mobile_ios_ui.ios.run') as run, \
                     self.assertRaises(ValueError):
                    ui.unlock(create)
                self.assertEqual(run.call_count,int(create and not attempted and phase=='unlock-start'))

    def test_owned_channel_matches_combined_accessibility_name_without_other_channels(self):
        for label in ('mobile-release', '#mobile-release', '# mobile-release', '#mobile-release 2'):
            self.assertTrue(android_ui.owned_channel(ET.Element('node', {'text':label})),label)
        for label in ('other-mobile-release', 'mobile-release-private', '#another-channel', 'private invitation'):
            self.assertFalse(android_ui.owned_channel(ET.Element('node', {'text':label})),label)

    def test_named_mobile_controls_accept_text_and_content_description(self):
        for attribute in ('text','content-desc'):
            self.assertTrue(android_ui.named_control(ET.Element('node',{attribute:'Network: Connected'}),'Network:'))
            self.assertTrue(android_ui.named_control(ET.Element('node',{attribute:'Files: 2'}),'Files:'))
            self.assertFalse(android_ui.named_control(ET.Element('node',{attribute:'Another control'}),'Network:'))

    def test_only_the_owned_system_pixel_launcher_anr_can_be_dismissed(self):
        xml='<hierarchy><node package="android" text="Pixel Launcher isn’t responding"/><node package="android" resource-id="android:id/aerr_close" bounds="[20,100][250,150]"/></hierarchy>'
        self.assertIsNotNone(android_ui.launcher_anr_close(ET.fromstring(xml)))
        for changed in (xml.replace('Pixel Launcher','GChat'),xml.replace('package="android"','package="boo.gchat.app"'),
                        xml.replace('aerr_close','aerr_wait'),xml.replace('[20,100][250,150]','[0,0][0,0]')):
            self.assertIsNone(android_ui.launcher_anr_close(ET.fromstring(changed)))
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            with patch.object(ui,'shell',side_effect=['','',xml]),patch.object(ui,'tap') as tap:
                self.assertEqual(ui.tree().tag,'hierarchy');tap.assert_called_once()
            self.assertEqual(ui.ui_observation['launcher_anr_dismissed'],1)
            ui.ui_observation['launcher_anr_dismissed']=2
            with patch.object(ui,'shell',side_effect=['','',xml]),patch.object(ui,'tap') as tap, \
                 self.assertRaisesRegex(ValueError,'launcher repeatedly'):
                ui.tree()
            tap.assert_not_called()

    def test_xctest_binding_accepts_only_fresh_owned_device_and_its_named_new_clone(self):
        old='10000000-0000-0000-0000-000000000000';base='20000000-0000-0000-0000-000000000000'
        clone='30000000-0000-0000-0000-000000000000';other='40000000-0000-0000-0000-000000000000'
        name='GChatAcceptance-owned'
        inventory={'devices':{'runtime':[{'udid':old,'name':'Existing device'},
            {'udid':base,'name':name},{'udid':clone,'name':'Clone 1 of '+name},
            {'udid':other,'name':'Another fresh device'}]}}
        self.assertEqual(owned_simulator_binding(base,base,name,{old},inventory),base)
        self.assertEqual(owned_simulator_binding(base,clone,name,{old},inventory),clone)
        for reported,before in ((old,{old}),(clone,{old,clone}),(other,{old}),('private-value',{old})):
            with self.subTest(reported=reported),self.assertRaises(ValueError):
                owned_simulator_binding(base,reported,name,before,inventory)

    def test_composer_requires_one_visible_owned_nonpassword_editable_field(self):
        field='<node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,400][290,450]"/>'
        tree=ET.fromstring('<hierarchy>'+field+'</hierarchy>')
        self.assertIsNotNone(android_ui.editable_composer(tree))
        for changed in (field+field,field.replace('boo.gchat.app','other.app'),
                        field.replace('/>',' password="true"/>'),field.replace('[10,400][290,450]','[0,0][0,0]')):
                self.assertIsNone(android_ui.editable_composer(ET.fromstring('<hierarchy>'+changed+'</hierarchy>')))

    def test_android_merged_message_labels_keep_complete_body_and_receipt_binding(self):
        body='mr-'+('a'*32);other='mr-'+('b'*32)
        self.assertEqual(android_ui.message_bodies(['[12:34] <sender> '+body],{body}),{body})
        for value in (body+'-suffix','prefix'+body,body+'0',other):
            self.assertEqual(android_ui.message_bodies([value],{body}),set())
        tree=ET.fromstring('<hierarchy><node content-desc="[12:34] &lt;mobile&gt; '+body+' · delivered"/></hierarchy>')
        self.assertTrue(delivery_row(tree,body,{body,other}))
        self.assertFalse(delivery_row(tree,other,{body,other}))
        tree=ET.fromstring('<hierarchy><node content-desc="'+body+'"/><node content-desc="'+other+' · delivered"/></hierarchy>')
        self.assertFalse(delivery_row(tree,body,{body,other}))

    def test_android_received_requires_its_own_app_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));body='mr-'+('a'*32)
            for package,expected in (('boo.gchat.app',True),('android',False)):
                tree=ET.fromstring('<hierarchy><node package="'+package+'" content-desc="[12:34] &lt;sender&gt; '+body+'"/></hierarchy>')
                with patch.object(ui,'tree',return_value=tree):self.assertEqual(ui.received(body),expected)

    def test_android_receive_view_diagnostics_keep_text_private_and_do_not_override_visibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));body='mr-'+('a'*32)
            tree=ET.fromstring('<hierarchy><node package="boo.gchat.app" content-desc="#mobile-release messages" '
                'bounds="[10,100][290,390]"><node package="boo.gchat.app" text="private conversation text"/>'
                '<node package="boo.gchat.app" text="*** Beginning of this conversation"/></node></hierarchy>')
            with patch.object(ui,'tree',return_value=tree),patch.object(ui,'rendered_lines',return_value=[]):
                self.assertFalse(ui.received(body))
            observation=ui.ui_observation['receive_view']
            self.assertTrue(observation['transcript_present']);self.assertTrue(observation['beginning_visible'])
            self.assertEqual(observation['transcript_nodes'],3)
            self.assertEqual(observation['transcript_bounds'],(10,100,290,390))
            self.assertNotIn('private',json.dumps(observation));self.assertNotIn(body,json.dumps(observation))

    def test_pixel_observer_excludes_text_outside_the_owned_transcript(self):
        header='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
        rows='5\t1\t1\t1\t1\t1\t10\t20\t50\t12\t95\tprivate-invitation\n'
        rows+='5\t1\t2\t1\t1\t1\t15\t130\t150\t12\t95\tmr-aaaaaaaaaaaaaaaa\n'
        rows+='5\t1\t2\t1\t1\t2\t170\t130\t70\t12\t95\tdelivered\n'
        lines=android_ui.pixel_lines(header+rows,(0,100,320,500))
        self.assertEqual(lines,[{'text':'mr-aaaaaaaaaaaaaaaa delivered','top':130,'bottom':142}])
        self.assertNotIn('private',json.dumps(lines))

    def test_wrapped_readable_canary_requires_every_exact_word_and_its_own_status(self):
        body='Canary apple arrow beach birch cloud dawn eagle forest grape river'
        first={'text':'[12:34] sender> Canary apple arrow beach birch','top':100,'bottom':112}
        second={'text':'cloud dawn eagle forest grape river','top':116,'bottom':128}
        receipt={'text':'· delivered','top':132,'bottom':144}
        self.assertTrue(android_ui.pixel_delivered([first,second,receipt],body,{body}))
        for changed in ({**second,'text':second['text'].replace('grape','grave')},
                        {**second,'top':170,'bottom':182},
                        {**second,'text':second['text']+' suffix'}):
            self.assertFalse(android_ui.pixel_delivered([first,changed,receipt],body,{body}))
        self.assertFalse(android_ui.pixel_delivered([receipt,first,second],body,{body}))
        self.assertFalse(android_ui.pixel_delivered([first,second,
            {**receipt,'text':'Canary other-message · delivered'}],body,{body}))
        self.assertEqual(android_ui.message_bodies([body.replace(' ', '\n')],{body}),{body})
        self.assertEqual(android_ui.message_bodies([body+'-suffix'],{body}),set())
        small_receipt={**receipt,'top':154,'bottom':165}
        self.assertTrue(android_ui.pixel_delivered([first,second,small_receipt],body,{body}))
        self.assertFalse(android_ui.pixel_delivered([first,second,
            {**small_receipt,'top':220,'bottom':231}],body,{body}))

    def test_pixel_delivery_diagnostics_do_not_expose_message_or_accept_storage_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary));body='Canary private test words'
            ui.bodies.add(body)
            lines=[{'text':body+' · stored by service','top':100,'bottom':112}]
            with patch.object(ui,'tree',return_value=ET.Element('hierarchy')), \
                 patch.object(ui,'rendered_lines',return_value=lines):
                self.assertFalse(ui.delivered(body))
            self.assertEqual(ui.ui_observation['pixel_delivery']['service_accepted_lines'],1)
            self.assertEqual(ui.ui_observation['pixel_delivery']['delivered_lines'],0)
            self.assertNotIn('private',json.dumps(ui.ui_observation))

    def test_pixel_receipt_remains_bound_to_one_complete_message_and_its_adjacent_status(self):
        body='mr-aaaaaaaaaaaaaaaa';other='mr-bbbbbbbbbbbbbbbb';known={body,other}
        line={'text':body,'top':100,'bottom':112}
        receipt={'text':'· delivered','top':116,'bottom':128}
        self.assertTrue(android_ui.pixel_delivered([line,receipt],body,known))
        self.assertTrue(android_ui.pixel_delivered([line,dict(receipt,top=100,bottom=112)],body,known))
        for changed in ([line,dict(receipt,top=200)],
                        [line,dict(receipt,text=other+' · delivered')],
                        [dict(line,text=body+'-suffix'),receipt],
                        [dict(line,text=body+' '+other+' delivered')],
                        [dict(line,text=other),receipt]):
            self.assertFalse(android_ui.pixel_delivered(changed,body,known))

    def test_receive_diagnostics_never_turn_a_timeout_into_a_pass_or_replace_it(self):
        for diagnostic_failure in (False,True):
            journey=MobileJourney.__new__(MobileJourney);sent=[];output={'events':[]}
            def history(_):
                if diagnostic_failure:raise ConnectionError('private error')
                return [{'body':sent[0],'mine':True,'delivery':'delivered'}]
            journey.peer=SimpleNamespace(submit=lambda _,body:sent.append(body),history=history)
            with patch.object(journey,'until',side_effect=TimeoutError('original UI deadline')), \
                 self.assertRaisesRegex(TimeoutError,'original UI deadline'):
                journey.ack(SimpleNamespace(received=lambda _:False),'baseline-initial',output)
            event=output['events'][0]
            self.assertEqual(event['event'],'rendered_receive_timeout')
            if diagnostic_failure:self.assertEqual(event['diagnostic_error'],'ConnectionError')
            else:self.assertIs(event['authenticated_recipient_ack'],True)
            self.assertNotIn('private error',json.dumps(output))

    def test_android_unlock_waits_for_the_unlocked_view_after_opening_feedback(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui,_,_=self.owned_android_ui(Path(temporary))
            opening=ET.fromstring('<hierarchy><node package="boo.gchat.app" text="Opening…"/></hierarchy>')
            connected=ET.fromstring('<hierarchy><node package="boo.gchat.app" text="Connect to GChat"/></hierarchy>')
            field=ET.fromstring('<node package="boo.gchat.app" password="true" bounds="[10,10][90,40]"/>')
            with patch.object(ui,'launch'),patch.object(ui,'node',return_value=field), \
                 patch.object(ui,'scroll_to_top'),patch.object(ui,'type'),patch.object(ui,'click'), \
                 patch.object(ui,'no_listener'),patch.object(ui,'tree',side_effect=[opening,connected]) as tree, \
                 patch.object(android_ui.time,'sleep'):
                ui.unlock(create=True)
            self.assertEqual(tree.call_count,2)

    def test_ios_invitation_form_uses_private_bridge_input_without_relaunch(self):
        ui=IOSUI.__new__(IOSUI);ui.device='owned-device'
        link='gcoms://join#GCIR1-fixture'
        with patch.object(ui,'stop') as stop,patch('mobile_ios_ui.subprocess.run') as process, \
             patch.object(ui,'call',side_effect=[True,True,'joined',True]) as call:
            ui.join(link)
        self.assertEqual([(c.args,c.kwargs) for c in call.call_args_list], [
            (('join_invitation',),{'invitation':link}), (('join_accept',),{}),
            (('join_connected',),{}), (('join_select',),{'joined':True})])
        stop.assert_not_called();process.assert_not_called()
        for invalid in ('https://private.invalid','gcoms:'+'x'*180000):
            with self.subTest(invalid_size=len(invalid)),patch.object(ui,'call') as call, \
                 self.assertRaisesRegex(ValueError,'bounded mobile'):
                ui.join(invalid)
            call.assert_not_called()

    def test_invitation_field_requires_the_owned_channel_preview_and_join_control(self):
        field='<node package="boo.gchat.app" class="android.widget.EditText" bounds="[10,100][290,150]"/>'
        preview='<node text="Join #mobile-release on Canary"/><node content-desc="Join"/>'
        self.assertIsNotNone(android_ui.invitation_nickname(ET.fromstring('<hierarchy>'+preview+field+'</hierarchy>')))
        for changed in (field, preview.replace('mobile-release','another-channel')+field,
                        preview.replace('Join"','Connect"')+field, preview+field+field):
            self.assertIsNone(android_ui.invitation_nickname(ET.fromstring('<hierarchy>'+changed+'</hierarchy>')))

    def test_ios_staged_join_requires_actual_admission_before_selection(self):
        for state in ('selected','joined',None,'unknown'):
            with self.subTest(state=state):
                ui=IOSUI.__new__(IOSUI)
                with patch.object(ui,'call',side_effect=[True,True,state,True]) as call:
                    if state in ('selected','joined'):ui.join('gcoms://join#GCIR1-private_fixture')
                    else:
                        with self.assertRaisesRegex(ValueError,'actual iOS enrollment'):ui.join('gcoms://join#GCIR1-private_fixture')
                self.assertEqual(call.call_count,4 if state in ('selected','joined') else 3)
                if call.call_count==4:self.assertEqual(call.call_args.kwargs,{'joined':state=='joined'})

    def test_xctest_startup_uses_setup_budget_before_issuing_ui_commands(self):
        bridge=Bridge()
        try:
            def started(_):bridge.polls=1
            with patch('mobile_ios_ui.time.sleep',side_effect=started):
                bridge.wait_running(time.monotonic()+5,lambda:True)
            bridge.polls=0
            with self.assertRaisesRegex(ValueError,'before readiness'):
                bridge.wait_running(time.monotonic()+5,lambda:False)
            with self.assertRaisesRegex(ValueError,'setup deadline'):
                bridge.wait_running(time.monotonic()-1,lambda:True)
            bridge.polls=1
            with self.assertRaisesRegex(ValueError,'late XCTest'):
                bridge.wait_running(time.monotonic()-1,lambda:True)
        finally:bridge.close()

    def test_ios_initial_install_is_retained_until_a_distinct_replacement(self):
        ui=IOSUI.__new__(IOSUI)
        ui.installed=False;ui.active_binary_sha256=None;ui.device='owned-device'
        ui.deadline=lambda:time.monotonic()+600
        baseline={'app':'baseline.app','binary_sha256':'a'*64}
        current={'app':'current.app','binary_sha256':'b'*64}
        with patch('mobile_ios_ui.ios.run') as run,patch.object(ui,'stop') as stop, \
             patch.object(ui,'installed_matches',return_value=True):
            ui.install(baseline)
            ui.install(baseline)
            stop.assert_not_called()
            self.assertEqual(run.call_count,1)
            ui.install(current)
            stop.assert_called_once()
            self.assertEqual(run.call_count,2)
        self.assertEqual(ui.active_binary_sha256,current['binary_sha256'])

    def test_ios_initial_setup_install_reserves_runner_budget_without_extending_setup(self):
        ui=IOSUI.__new__(IOSUI);ui.deadline=lambda:600
        for now,maximum in ((0,240),(300,180),(450,30)):
            with self.subTest(now=now),patch('mobile_ios_ui.time.monotonic',return_value=now), \
                 patch.object(ui,'install') as install:
                ui.setup_install({'app':'retained.app'})
                self.assertEqual(install.call_args.kwargs,{'maximum':maximum})
                self.assertLessEqual(now+maximum+120,600)
        with patch('mobile_ios_ui.time.monotonic',return_value=460), \
             patch.object(ui,'install') as install,self.assertRaisesRegex(ValueError,'setup deadline'):
            ui.setup_install({'app':'retained.app'})
        install.assert_not_called()

    def test_ios_export_reunlock_has_exact_owned_clipboard_and_always_clears_it(self):
        for failed in (False,True):
            with self.subTest(failed=failed):
                ui=IOSUI.__new__(IOSUI);ui.passphrase='fixture-private-passphrase'
                ui.runner=SimpleNamespace(poll=lambda:None);ui.deadline=lambda:time.monotonic()+600
                ui.bridge=SimpleNamespace(call=lambda *a,**k:None)
                with patch.object(ui,'copy_input') as copied, \
                     patch.object(ui.bridge,'call',side_effect=ValueError('UI failure') if failed else None):
                    if failed:
                        with self.assertRaisesRegex(ValueError,'UI failure'):ui.call('export',name='baseline-cache.bin')
                    else:ui.call('export',name='baseline-cache.bin')
                self.assertEqual([c.args[0] for c in copied.call_args_list],['fixture-private-passphrase',''])

    def test_ios_initial_setup_install_still_requires_hash_before_its_own_deadline(self):
        import subprocess
        ui=IOSUI.__new__(IOSUI);ui.device='owned';ui.installed=False
        ui.active_binary_sha256=None;ui.deadline=lambda:600
        item={'app':'retained.app','binary_sha256':'a'*64};clock=[0.0]
        def install(*args,**kwargs):
            clock[0]+=kwargs['timeout']
            raise subprocess.TimeoutExpired('simctl',kwargs['timeout'])
        def observe(*args):clock[0]+=5;return False
        with patch('mobile_ios_ui.time.monotonic',side_effect=lambda:clock[0]), \
             patch('mobile_ios_ui.ios.run',side_effect=install) as run, \
             patch.object(ui,'installed_matches',side_effect=observe),self.assertRaises(TimeoutError):
            ui.setup_install(item)
        self.assertEqual([c.kwargs['timeout'] for c in run.call_args_list],[40,175])
        self.assertLess(clock[0],240);self.assertFalse(ui.installed)

    def test_ios_install_timeout_reconciles_exact_executable_without_reinstall(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            app=Path(temporary);binary=app/'GChat';binary.write_bytes(b'retained native bytes')
            item={'app':app,'binary':binary,'binary_sha256':inputs.digest(binary)}
            ui=IOSUI.__new__(IOSUI);ui.device='owned';ui.installed=False
            ui.active_binary_sha256=None;ui.deadline=lambda:time.monotonic()+600
            with patch('mobile_ios_ui.ios.run',side_effect=subprocess.TimeoutExpired('simctl',40)) as run, \
                 patch('mobile_ios_ui.ios.output',return_value=str(app)) as output:
                ui.install(item)
            self.assertEqual(run.call_count,1)
            self.assertTrue(ui.install_observation['hash_verified'])
            self.assertEqual(ui.install_observation['timeouts'],1)
            self.assertEqual(output.call_args.kwargs['timeout'],10)
            self.assertEqual(ui.active_binary_sha256,item['binary_sha256'])

    def test_ios_install_retry_cannot_extend_original_deadline_or_accept_wrong_binary(self):
        import subprocess
        ui=IOSUI.__new__(IOSUI);ui.device='owned';ui.installed=False
        ui.active_binary_sha256=None;ui.deadline=lambda:120
        item={'app':'retained.app','binary':'retained.app/GChat','binary_sha256':'a'*64}
        clock=[0.0]
        def install(*args,**kwargs):
            clock[0]+=kwargs['timeout']
            raise subprocess.TimeoutExpired('simctl',kwargs['timeout'])
        def observe(*args):clock[0]+=5;return False
        with patch('mobile_ios_ui.time.monotonic',side_effect=lambda:clock[0]), \
             patch('mobile_ios_ui.ios.run',side_effect=install) as run, \
             patch.object(ui,'installed_matches',side_effect=observe),self.assertRaises(TimeoutError):
            ui.install(item)
        self.assertEqual([c.kwargs['timeout'] for c in run.call_args_list],[40,55])
        self.assertLessEqual(clock[0],120)
        self.assertFalse(ui.installed)
        with tempfile.TemporaryDirectory() as temporary:
            app=Path(temporary);(app/'GChat').write_bytes(b'substituted executable')
            with patch('mobile_ios_ui.ios.output',return_value=str(app)), \
                 self.assertRaisesRegex(ValueError,'differs from retained'):
                ui.installed_matches(item,time.monotonic()+10)

    def test_ios_install_refuses_exhausted_budget_and_does_not_retry_command_errors(self):
        import subprocess
        ui=IOSUI.__new__(IOSUI);ui.device='owned';ui.installed=False
        ui.active_binary_sha256=None;ui.deadline=lambda:time.monotonic()-1
        item={'app':'retained.app','binary_sha256':'a'*64}
        with patch('mobile_ios_ui.ios.run') as run,self.assertRaisesRegex(ValueError,'install deadline'):
            ui.install(item)
        run.assert_not_called()
        ui.deadline=lambda:time.monotonic()+600
        with patch('mobile_ios_ui.ios.run',side_effect=subprocess.CalledProcessError(1,'simctl')) as run, \
             patch.object(ui,'installed_matches') as observe,self.assertRaises(subprocess.CalledProcessError):
            ui.install(item)
        self.assertEqual(run.call_count,1);observe.assert_not_called()

    def test_ios_matching_installed_executable_cannot_qualify_after_original_deadline(self):
        with tempfile.TemporaryDirectory() as temporary:
            app=Path(temporary);binary=app/'GChat';binary.write_bytes(b'retained executable')
            item={'binary':binary,'binary_sha256':inputs.digest(binary)}
            ui=IOSUI.__new__(IOSUI);ui.device='owned'
            with patch('mobile_ios_ui.ios.output',return_value=str(app)), \
                 patch('mobile_ios_ui.time.monotonic',side_effect=[0,120]), \
                 self.assertRaisesRegex(ValueError,'late simulator install observation'):
                ui.installed_matches(item,120)

    def test_failed_device_check_does_not_hide_actual_peer_cleanup_or_become_a_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'c0').mkdir()
            journey=MobileJourney.__new__(MobileJourney)
            journey.peer=SimpleNamespace(children=[],clients=[0],root=root)
            journey.rollback={'passed':False};journey.report={'passed':False}
            ui=SimpleNamespace(cleanup=lambda:{'passed':False})
            self.assertEqual(journey.cleanup(ui),[])
            self.assertTrue(journey.report['children_stopped'])
            self.assertTrue(journey.report['temporary_profile_removed'])
            self.assertFalse(journey.report['passed'])
            self.assertFalse(journey.rollback['cleanup_complete'])

    def test_completed_file_observation_cannot_use_another_file_or_downloading_state(self):
        tree=ET.fromstring('<hierarchy><node><node text="baseline-cache.bin"/>'
            '<node text="262,144 bytes · complete · 1 offering peers"/></node>'
            '<node><node text="bounded-mobile.bin"/>'
            '<node text="16.0 MiB · downloading · 1 offering peers"/></node></hierarchy>')
        names={'baseline-cache.bin','bounded-mobile.bin'}
        self.assertTrue(android_ui.completed_file_row(tree,'baseline-cache.bin',names))
        self.assertFalse(android_ui.completed_file_row(tree,'bounded-mobile.bin',names))
        self.assertFalse(android_ui.completed_file_row(tree,'absent.bin',names))

    def test_file_action_closes_its_files_dialog_after_accept_without_dismissing_picker(self):
        for action in ('Download & share','Save file…'):
            with self.subTest(action=action),tempfile.TemporaryDirectory() as temporary:
                ui,_,_=self.owned_android_ui(Path(temporary))
                tree=ET.fromstring('<hierarchy><node><node text="baseline-cache.bin"/>'
                    f'<node text="{action.replace("&","&amp;")}" bounds="[10,10][90,50]"/>'
                    '</node></hierarchy>')
                with patch.object(ui,'node',return_value=ET.Element('node')),patch.object(ui,'tap'), \
                     patch.object(ui,'tree',return_value=tree),patch.object(ui,'click') as click:
                    ui.file_action('baseline-cache.bin',action)
                if action=='Save file…':click.assert_not_called()
                else:click.assert_called_once_with('Close dialog')

    def test_mobile_inputs_require_distinct_releases_and_matching_native_peer(self):
        for target in ('android', 'ios'):
            _, specs, *_ = mobile_fixture(target)
            self.assertEqual(inputs.validate_inputs(specs), specs)
            for field in ('run', 'artifact', 'archive', 'sources'):
                changed = copy.deepcopy(specs)
                changed['baseline'][field] = changed['current'][field]
                with self.subTest(target=target, field=field), self.assertRaises(ValueError):
                    inputs.validate_inputs(changed)
            for field, value in (('peer_target', 'windows-x86_64'), ('target', 'linux-x86_64')):
                changed = copy.deepcopy(specs)
                changed[field] = value
                with self.assertRaises(ValueError):
                    inputs.validate_inputs(changed)
            changed = copy.deepcopy(specs)
            changed['peer']['sources']['gcoms'] = '0' * 40
            with self.assertRaises(ValueError):
                inputs.validate_inputs(changed)

    def test_provider_identity_and_escaping_paths_fail_before_native_mutation(self):
        _, specs, *_ = mobile_fixture()
        for field, value in (('run', True), ('artifact', 0), ('conclusion', 'failure'),
                             ('controller', 'main'), ('archive', 'unverified'),
                             ('manifest', '../build.json'), ('manifest', '/build.json'),
                             ('manifest', r'C:\build.json'), ('manifest', 'report.json')):
            changed = copy.deepcopy(specs['current'])
            changed[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                inputs.validate_provider(changed)

    def test_real_mobile_ui_and_unchanged_ciphertext_are_required_for_receipt(self):
        for target in ('android', 'ios'):
            manifest, specs, report, rollback, network = mobile_fixture(target)
            acceptance.qualify_native(report, rollback, network, manifest, target, specs, 110)
            for field, bad in (('ui_driven', False), ('application_resigned', True),
                               ('physical_device_qualified', True)):
                changed = copy.deepcopy(report)
                changed[field] = bad
                with self.subTest(target=target, field=field), self.assertRaises(ValueError):
                    acceptance.qualify_native(changed, rollback, network, manifest, target, specs, 110)
            for bad in ('unverified', '8' * 64):
                changed = copy.deepcopy(rollback)
                changed['phases'][1]['encrypted_cache_sha256'] = bad
                with self.assertRaises(ValueError):
                    acceptance.qualify_native(report, changed, network, manifest, target, specs, 110)
            changed = copy.deepcopy(rollback)
            for phase in changed['phases']:
                phase['encrypted_cache_sha256'] = phase['cache_sha256']
            with self.assertRaises(ValueError):
                acceptance.qualify_native(report, changed, network, manifest, target, specs, 110)
            with self.assertRaises(ValueError):
                acceptance.qualify_native({**report,'installation_cleanup':[]},rollback,network,
                                          manifest,target,specs,110)

    def test_desktop_or_ordinary_picker_receipt_cannot_qualify_mobile(self):
        manifest, specs, report, rollback, network = mobile_fixture()
        for changed in ({**report, 'platform': 'linux-x86_64'},
                        {**report, 'ui_driven': None},
                        {**report, 'passed': False}):
            with self.assertRaises(ValueError):
                acceptance.qualify_native(changed, rollback, network, manifest, 'android', specs, 110)
        changed = copy.deepcopy(network)
        changed['file_check']['bytes'] = 262144
        with self.assertRaises(ValueError):
            acceptance.qualify_native(report, rollback, changed, manifest, 'android', specs, 110)

    def test_delivery_suffix_for_another_message_is_not_a_receipt(self):
        tree = ET.fromstring('<hierarchy><node><node><node text="mr-old"/>'
                            '<node text=" · delivered"/></node><node><node text="mr-new"/>'
                            '<node text=" · accepted locally"/></node></node></hierarchy>')
        self.assertFalse(delivery_row(tree, 'mr-new', {'mr-new', 'mr-old'}))
        self.assertTrue(delivery_row(tree, 'mr-old', {'mr-new', 'mr-old'}))
        tree.find('.//node[@text=" · delivered"]').set('text', '· delivered')
        self.assertTrue(delivery_row(tree, 'mr-old', {'mr-new', 'mr-old'}))
        missing = ET.fromstring('<hierarchy><node text=" · delivered"/></hierarchy>')
        self.assertFalse(delivery_row(missing, 'mr-new', {'mr-new'}))

    def test_xctest_bridge_requires_its_private_token_and_one_matching_result(self):
        bridge = Bridge()
        answers = []
        def post(path, value, token=None):
            headers = {'Content-Type': 'application/json',
                       'Authorization': 'Bearer ' + (bridge.token if token is None else token)}
            request = Request(bridge.url + path, data=json.dumps(value).encode(), headers=headers)
            with urlopen(request, timeout=5) as response:
                return json.load(response)
        worker = threading.Thread(target=lambda: answers.append(bridge.call('ready', timeout=5)))
        try:
            with self.assertRaises(HTTPError) as denied:
                post('/next', {'ready': True}, token='wrong')
            self.assertEqual(denied.exception.code, 403)
            denied.exception.close()
            worker.start()
            command = post('/next', {'ready': True})
            with self.assertRaises(HTTPError) as unknown:
                post('/result', {'id': '0' * 32, 'passed': True})
            self.assertEqual(unknown.exception.code, 400)
            unknown.exception.close()
            self.assertEqual(post('/result', {'id': command['id'], 'passed': True, 'value': True}),
                             {'accepted': True})
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(answers, [True])
            self.assertEqual(bridge.polls,1)
            with self.assertRaises(HTTPError) as duplicate:
                post('/result', {'id': command['id'], 'passed': True, 'value': True})
            self.assertEqual(duplicate.exception.code, 400)
            duplicate.exception.close()
            with self.assertRaisesRegex(ValueError, 'original XCTest command deadline'):
                bridge.call('ready', timeout=0.02)
        finally:
            worker.join(timeout=5) if worker.ident is not None else None
            bridge.close()

    def test_xctest_bridge_stops_waiting_when_its_owned_runner_exits(self):
        bridge=Bridge()
        try:
            with self.assertRaisesRegex(ValueError,'owned XCTest runner exited'):
                bridge.call('ready',timeout=60,alive=lambda:False)
        finally:
            bridge.close()

    def test_xctest_failure_phase_is_public_and_private_values_are_rejected(self):
        bridge=Bridge();errors=[]
        def caller():
            try:bridge.call('join',timeout=5)
            except ValueError as error:errors.append(error)
        def post(path,value):
            request=Request(bridge.url+path,data=json.dumps(value).encode(),headers={
                'Content-Type':'application/json','Authorization':'Bearer '+bridge.token})
            with urlopen(request,timeout=5) as response:return json.load(response)
        worker=threading.Thread(target=caller)
        try:
            worker.start();command=post('/next',{'ready':True})
            with self.assertRaises(HTTPError) as denied:
                post('/result',{'id':command['id'],'passed':False,'phase':'private-invitation'})
            self.assertEqual(denied.exception.code,400);denied.exception.close()
            for observation in ({'private-invitation':True}, {'reconnect':'private-value'}):
                with self.assertRaises(HTTPError) as denied:
                    post('/result',{'id':command['id'],'passed':False,'phase':'join-preview',
                                    'observation':observation})
                self.assertEqual(denied.exception.code,400);denied.exception.close()
            post('/result',{'id':command['id'],'passed':False,'phase':'join-preview',
                            'observation':{'reconnect':True,'review_invitation':False}})
            worker.join(timeout=5)
            self.assertEqual(len(errors),1)
            self.assertEqual(errors[0].ios_observation_phase,'join-preview')
            self.assertEqual(errors[0].ios_observation_controls,{'reconnect':True,'review_invitation':False})
            self.assertNotIn('private',str(errors[0]))
        finally:
            worker.join(timeout=5) if worker.ident is not None else None
            bridge.close()

    def test_ios_runner_diagnostics_exclude_private_logs_and_retain_static_failure_categories(self):
        with tempfile.TemporaryDirectory() as temporary:
            log=Path(temporary)/'xctest.private.log'
            log.write_text('private-token private-invitation /private/profile/path\n'
                '/private/build/AcceptanceTests.swift:44:9: error: private error text\n'
                '/private/build/AcceptanceTests.swift:282: error: Failed to tap private text\n'
                'GCHAT_ACCEPTANCE_BRIDGE_CONFIGURATION=1\n'
                'GCHAT_ACCEPTANCE_BRIDGE_TRANSPORT=-1022\n'
                'GCHAT_ACCEPTANCE_UI_PHASE=join-arrival\n'
                'GCHAT_ACCEPTANCE_UI_PHASE=identity-network\n'
                'GCHAT_ACCEPTANCE_OBSERVATION_FAILURE=72\n'
                'GCHAT_ACCEPTANCE_INPUT_VALUE_LENGTH=12\n'
                'GCHAT_ACCEPTANCE_INPUT_PRIVATE=123\n'
                'GCHAT_ACCEPTANCE_UI_PHASE=private-invitation\n'
                'GCHAT_ACCEPTANCE_BRIDGE_HTTP=403\n** TEST BUILD FAILED **\n')
            result=runner_diagnostics(log,65,0)
            self.assertEqual(result,{'exit_code':65,'bridge_polls':0,'compile_error_locations':['44:9'],
                'runtime_error_locations':['282'],
                'observation_failure_lines':[72],
                'input_value_diagnostics':{'value_length':12},
                'ui_error_categories':{'tap_failed':True,'snapshot_failed':False,'not_hittable':False,'no_matches':False},
                'configuration_ready':True,'transport_codes':[-1022],'http_status_codes':[403],
                'ui_phases':['join-arrival','identity-network'],'build_failed':True,
                'runner_progress':{'swift_compile':False,'link':False,'build_description':False,
                    'testing_started':False,'runner_launch_failure':False,'simulator_failure':False,'test_failure':False}})
            self.assertNotIn('private',json.dumps(result))

    def test_post_journey_artifact_check_observes_changed_bytes(self):
        driver = module('test-mobile-upgrade')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / 'native'
            binary.write_bytes(b'original')
            item = {'binary': binary, 'binary_sha256': hashlib.sha256(b'original').hexdigest()}
            self.assertTrue(driver.unchanged([item], 'ios'))
            binary.write_bytes(b'changed')
            self.assertFalse(driver.unchanged([item], 'ios'))

    def test_mobile_dispatch_uses_its_own_workflow_and_retains_unknown_reply(self):
        manifest, specs, *_ = mobile_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grant = root / 'grant.json'
            grant.write_text('{}')
            providers = {target: specs['current'] for target in ('android', 'linux-x86_64')}
            def api(path, **kwargs):
                return {'workflow_runs': []}
            with patch.object(acceptance, 'provider', side_effect=lambda state, manifest, target: providers[target]), \
                 patch.object(acceptance, 'baseline', return_value=specs['baseline']), \
                 patch.object(acceptance, 'gh', side_effect=api) as provider_api, \
                 patch.object(acceptance, 'ssh', return_value=b'{"invitation":"fixture-no-authority"}'), \
                 patch.object(acceptance.subprocess, 'run'):
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant), 'qualification_commit': None},
                                                     manifest, 'android', root, '1' * 64))
                marker = json.loads((root / 'acceptance-intent.json').read_text())
                self.assertTrue(marker['dispatch_reserved'])
                self.assertEqual(marker['inputs']['peer_target'], 'linux-x86_64')
                self.assertNotIn('invitation', marker)
                calls = [call for call in provider_api.call_args_list if call.args[0].endswith('/dispatches')]
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args[0], 'actions/workflows/mobile-acceptance.yml/dispatches')
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant), 'qualification_commit': None},
                                                     manifest, 'android', root, '1' * 64))
                self.assertEqual(sum(call.args[0].endswith('/dispatches')
                                     for call in provider_api.call_args_list), 1)

    def test_missing_current_native_peer_waits_without_issuing_a_grant(self):
        manifest, specs, *_ = mobile_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grant = root / 'grant.json'
            grant.write_text('{}')
            with patch.object(acceptance, 'provider', side_effect=[specs['current'], None]), \
                 patch.object(acceptance, 'baseline', return_value=specs['baseline']), \
                 patch.object(acceptance, 'ssh') as ssh:
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant)},
                                                     manifest, 'android', root, '1' * 64))
                ssh.assert_not_called()
                self.assertFalse((root / 'acceptance-intent.json').exists())


if __name__ == '__main__':
    unittest.main()
