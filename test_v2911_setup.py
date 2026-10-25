import tempfile
import unittest
from pathlib import Path
from setup_telegram import write_credentials
class CredentialSetupTests(unittest.TestCase):
    def test_writes_safe_cmd(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'CREDENTIALS.cmd'
            token = '123456789:' + 'Abcdef_ghi1234567890123456'
            write_credentials(token,p)
            value = p.read_text()
            self.assertIn(f'set "TELEGRAM_BOT_TOKEN={token}"',value)
            self.assertIn('@EgoniaSignalsFree',value)
    def test_rejects_shell_injection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'CREDENTIALS.cmd'
            for s in ('','foo', '12345:abc&whoami', '12345:abc" & echo bad'):
                with self.assertRaises(ValueError):write_credentials(s,p)
            self.assertFalse(p.exists())
if __name__ == '__main__':unittest.main()
