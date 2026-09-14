import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import enquiry_api
import server

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL', '')
# These tests drop and recreate the enquiry tables, so they must never touch a real database.
if TEST_DATABASE_URL and TEST_DATABASE_URL == os.environ.get('DATABASE_URL'):
    raise RuntimeError('TEST_DATABASE_URL must be a disposable database, not DATABASE_URL.')

@unittest.skipUnless(TEST_DATABASE_URL, 'set TEST_DATABASE_URL to a disposable PostgreSQL database')
class EnquiryTests(unittest.TestCase):
    def setUp(self):
        for patcher in (patch.dict(os.environ, {'DATABASE_URL': TEST_DATABASE_URL,
                                                'VOICE_ALLOWED_ORIGIN': 'http://localhost:8000',
                                                'ENQUIRY_TO_EMAIL': 'team@example.com',
                                                'SMTP_HOST': 'smtp.example.com', 'SMTP_PORT': '587'}),
                        # Ignore the developer's local .env so only these values are in play.
                        patch('chat_api.dotenv_values', return_value={}),
                        patch.object(enquiry_api, '_schema_ready', False)):
            patcher.start(); self.addCleanup(patcher.stop)
        with enquiry_api.transaction() as cursor:
            cursor.execute('DROP TABLE IF EXISTS website_enquiries, website_schema_migrations')
        smtp = patch('enquiry_api.smtplib.SMTP')
        self.smtp = smtp.start(); self.addCleanup(smtp.stop)
        enquiry_api.attempts.clear()
        self.client = TestClient(server.app)
        self.headers = {'origin': 'http://localhost:8000'}
        self.body = {'name': 'Asha', 'company': 'City Hospital', 'email': 'asha@hospital.example',
                     'problem': 'We send appointment reminders by hand.'}

    def send(self, **changes):
        return self.client.post('/api/enquiry', headers=self.headers, json={**self.body, **changes})

    def query(self, sql):
        enquiry_api.ensure_schema()
        with enquiry_api.transaction() as cursor:
            cursor.execute(sql)
            return [tuple(row) for row in cursor.fetchall()]

    def rows(self):
        return self.query('SELECT name, company, email, problem, emailed FROM website_enquiries ORDER BY id')

    def test_saves_and_emails_team(self):
        self.assertEqual(self.send(name='  Asha  ').status_code, 200)
        self.assertEqual(self.rows(), [('Asha', 'City Hospital', 'asha@hospital.example',
                                        'We send appointment reminders by hand.', True)])
        self.assertEqual(self.query('SELECT count(*) FROM website_enquiries WHERE created_at IS NOT NULL'), [(1,)])
        message = self.smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        self.assertEqual(message['To'], 'team@example.com')
        self.assertEqual(message['Reply-To'], 'asha@hospital.example')
        self.assertIn('appointment reminders', message.get_content())

    def test_email_failure_keeps_enquiry(self):
        self.smtp.side_effect = OSError('SMTP unreachable')
        with self.assertLogs('uvicorn.error', 'WARNING'):
            self.assertEqual(self.send().status_code, 200)
        self.assertEqual(self.rows()[0][-1], False)

    def test_validation_origin_and_honeypot(self):
        self.assertEqual(self.client.post('/api/enquiry', json=self.body).status_code, 403)
        self.assertEqual(self.send(email='not-an-email').status_code, 422)
        self.assertEqual(self.send(name='Asha\nBcc: x@example.com').status_code, 422)
        self.assertEqual(self.send(problem='   ').status_code, 422)
        self.assertEqual(self.send(problem='x' * 2001).status_code, 422)
        self.assertEqual(self.send(website='http://spam.example').status_code, 200)
        self.assertEqual(self.rows(), [])
        self.assertFalse(self.smtp.called)
        self.assertEqual(self.client.get('/enquiries.sqlite3').status_code, 404)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.send().status_code, 200)
        self.assertEqual(self.send().status_code, 429)
        self.assertEqual(len(self.rows()), 5)

    def test_schema_migration_is_idempotent(self):
        # An earlier deploy may already have created the table before migrations were recorded.
        with enquiry_api.transaction() as cursor:
            cursor.execute(enquiry_api.MIGRATIONS[0][1])
        for _ in range(2):
            enquiry_api._schema_ready = False
            enquiry_api.ensure_schema()
        self.assertEqual(self.query('SELECT version FROM website_schema_migrations'), [(1,)])
        self.assertEqual(self.send().status_code, 200)
        self.assertEqual(len(self.rows()), 1)

if __name__ == '__main__': unittest.main()
