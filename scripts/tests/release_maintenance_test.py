from pathlib import Path
from contextlib import closing
import datetime,hashlib,os,shutil,sqlite3,subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_maintenance import refresh_apt,maintain
from release_ledger import Ledger
from release_signatures import verify

class MaintenanceTests(unittest.TestCase):
    def test_daily_database_backup_is_consistent_and_never_removes_job_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);ledger=Ledger(root/'ledger.sqlite')
            try:
                jobs=root/'jobs';jobs.mkdir();evidence=jobs/'receipt';evidence.write_text('keep')
                maintain(root,ledger,{})
                backups=list((root/'backups').glob('*.sqlite'));self.assertEqual(len(backups),1)
                with closing(sqlite3.connect(backups[0])) as copy:self.assertEqual(copy.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                maintain(root,ledger,{})
                self.assertEqual(len(list((root/'backups').glob('*.sqlite'))),1);self.assertEqual(evidence.read_text(),'keep')
            finally:ledger.close()

    @unittest.skipUnless(os.name == 'posix' and shutil.which('gpg'),'POSIX APT publisher and native GPG required')
    def test_refresh_verifies_old_index_and_preserves_package_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);home=root/'gnupg';home.mkdir(mode=0o700)
            with patch.dict(os.environ,{'GNUPGHOME':str(home)},clear=False):
                subprocess.run(['gpg','--batch','--pinentry-mode','loopback','--passphrase','','--quick-generate-key','Fixture <fixture@example.invalid>','ed25519','sign','1d'],check=True,capture_output=True)
                listing=subprocess.check_output(['gpg','--batch','--with-colons','--list-secret-keys'],text=True,stderr=subprocess.DEVNULL)
                key=next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
                output=root/'apt';snapshot=output/'snapshots/original';binary=snapshot/'main/binary-amd64';binary.mkdir(parents=True)
                packages=b'Package: g-chat\nVersion: 1.0.0\n';(binary/'Packages').write_bytes(packages)
                original='Date: Mon, 01 Jan 2024 00:00:00 +0000\nValid-Until: Mon, 08 Jan 2024 00:00:00 +0000\nSHA256:\n '+hashlib.sha256(packages).hexdigest()+' '+str(len(packages))+' main/binary-amd64/Packages\n'
                (snapshot/'Release').write_text(original)
                subprocess.run(['gpg','--batch','--yes','--detach-sign','--armor','--local-user',key,'--output',str(snapshot/'Release.gpg'),str(snapshot/'Release')],check=True,capture_output=True)
                stable=output/'dists/stable';stable.parent.mkdir();stable.symlink_to('../snapshots/original')
                now=datetime.datetime(2024,1,7,tzinfo=datetime.timezone.utc)
                self.assertTrue(refresh_apt(output,key,now))
                self.assertEqual((stable/'main/binary-amd64/Packages').read_bytes(),packages)
                verify(stable/'Release.gpg',stable/'Release',key)
                self.assertFalse(refresh_apt(output,key,now))
                (stable/'main/binary-amd64/Packages').write_bytes(b'tamper')
                with self.assertRaisesRegex(ValueError,'index changed'):refresh_apt(output,key,now+datetime.timedelta(days=8))
