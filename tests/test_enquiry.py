import os
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import enquiry_api
import server

class EnquiryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        for patcher in (patch.object(enquiry_api, 'DB_PATH', Path(self.tmp.name) / 'enquiries.db'),
                        patch.dict(os.environ, {'VOICE_ALLOWED_ORIGIN': 'http://localhost:8000',
                                                'ENQUIRY_TO_EMAIL': 'team@example.com',
                                                'SMTP_HOST': 'smtp.example.com', 'SMTP_PORT': '587'})):
            patcher.start(); self.addCleanup(patcher.stop)
        smtp = patch('enquiry_api.smtplib.SMTP')
        self.smtp = smtp.start(); self.addCleanup(smtp.stop)
        enquiry_api.attempts.clear()
        self.client = TestClient(server.app)
        self.headers = {'origin': 'http://localhost:8000'}
        self.body = {'name': 'Asha', 'company': 'Acme Logistics', 'email': 'asha@acme.example',
                     'problem': 'We retype delivery notes into our ERP.'}

    def send(self, **changes):
        return self.client.post('/api/enquiry', headers=self.headers, json={**self.body, **changes})

    def rows(self):
        with closing(enquiry_api.connect()) as db:
            return db.execute('SELECT name, company, email, problem, emailed FROM enquiries').fetchall()

    def test_saves_and_emails_team(self):
        self.assertEqual(self.send(name='  Asha  ').status_code, 200)
        self.assertEqual(self.rows(), [('Asha', 'Acme Logistics', 'asha@acme.example',
                                        'We retype delivery notes into our ERP.', 1)])
        message = self.smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        self.assertEqual(message['To'], 'team@example.com')
        self.assertEqual(message['Reply-To'], 'asha@acme.example')
        self.assertIn('We retype delivery notes', message.get_content())

    def test_email_failure_keeps_enquiry(self):
        self.smtp.side_effect = OSError('SMTP unreachable')
        with self.assertLogs('uvicorn.error', 'WARNING'):
            self.assertEqual(self.send().status_code, 200)
        self.assertEqual(self.rows()[0][-1], 0)

    def test_validation_origin_and_honeypot(self):
        self.assertEqual(self.client.post('/api/enquiry', json=self.body).status_code, 403)
        self.assertEqual(self.send(email='not-an-email').status_code, 422)
        self.assertEqual(self.send(name='Asha\nBcc: x@example.com').status_code, 422)
        self.assertEqual(self.send(problem='   ').status_code, 422)
        self.assertEqual(self.send(website='http://spam.example').status_code, 200)
        self.assertEqual(self.rows(), [])
        self.assertFalse(self.smtp.called)
        self.assertEqual(self.client.get('/enquiries.sqlite3').status_code, 404)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.send().status_code, 200)
        self.assertEqual(self.send().status_code, 429)
        self.assertEqual(len(self.rows()), 5)

if __name__ == '__main__': unittest.main()
