import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import jwt
from fastapi.testclient import TestClient
import chat_api
import enquiry_api
import server

APEX, WWW = 'https://optimizerstep.com', 'https://www.optimizerstep.com'
SECRETS = {
    'LIVEKIT_API_SECRET': 'sentinel-livekit-secret-0123456789abcdef0123',
    'OPENAI_API_KEY': 'sentinel-openai-key',
    'SARVAM_API_KEY': 'sentinel-sarvam-key',
    'SMTP_PASSWORD': 'sentinel-smtp-password',
    # Nothing listens on port 1, so enquiries exercise the database-unavailable path.
    'DATABASE_URL': 'postgresql://website:sentinel-db-password@127.0.0.1:1/website',
}
ENQUIRY = {'name': 'Asha', 'company': 'City Hospital', 'email': 'asha@hospital.example',
           'problem': 'We send appointment reminders by hand.'}

class ProductionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(tmp.cleanup)
        env = {**SECRETS, 'LIVEKIT_URL': 'wss://optimizer.livekit.cloud', 'LIVEKIT_API_KEY': 'APIsentinel',
               'VOICE_ALLOWED_ORIGIN': f'{APEX}, {WWW}/', 'ENQUIRY_TO_EMAIL': 'team@example.com',
               'SMTP_HOST': 'smtp.example.com'}
        for patcher in (patch.dict(os.environ, env),
                        # Ignore the developer's local .env so only these values are in play.
                        patch('chat_api.dotenv_values', return_value={}),
                        patch.object(chat_api, 'DB_PATH', Path(tmp.name) / 'usage.db'),
                        patch.object(enquiry_api, '_schema_ready', False)):
            patcher.start(); self.addCleanup(patcher.stop)
        server.attempts.clear()
        enquiry_api.attempts.clear()
        self.client = TestClient(server.app, base_url=APEX)

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_course_pages_and_playground_modules(self):
        for path in ('/', '/playground'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn('ML Playground', response.text)
        for path in ('/app.js', '/playground.js', '/launchCampaign.js', '/styles.css'):
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_docs_and_schema_are_not_public(self):
        for path in ('/docs', '/redoc', '/openapi.json'):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_security_headers_and_hsts_only_over_https(self):
        headers = self.client.get('/').headers
        self.assertEqual(headers['x-content-type-options'], 'nosniff')
        self.assertEqual(headers['strict-transport-security'], 'max-age=31536000')
        self.assertIn('microphone=(self)', headers['permissions-policy'])
        self.assertNotIn('strict-transport-security', TestClient(server.app).get('/').headers)

    def test_custom_domain_origins(self):
        for origin, expected in ((APEX, 200), (WWW, 200), ('http://optimizerstep.com', 403), ('https://evil.example', 403)):
            server.attempts.clear()
            response = self.client.post('/api/voice/token', headers={'origin': origin}, json={'language': 'en-IN'})
            self.assertEqual(response.status_code, expected, origin)
        self.assertEqual(self.client.post('/api/enquiry', headers={'origin': 'https://evil.example'}, json=ENQUIRY).status_code, 403)

    def test_livekit_token_is_signed_server_side(self):
        response = self.client.post('/api/voice/token', headers={'origin': APEX}, json={'language': 'en-IN'})
        self.assertEqual(set(response.json()), {'server_url', 'participant_token', 'duration_seconds'})
        claims = jwt.decode(response.json()['participant_token'], SECRETS['LIVEKIT_API_SECRET'], algorithms=['HS256'])
        self.assertEqual(claims['iss'], 'APIsentinel')
        self.assertEqual(claims['video']['canPublishSources'], ['microphone'])

    def test_enquiry_database_outage_returns_503(self):
        with self.assertLogs('uvicorn.error', 'ERROR'):
            response = self.client.post('/api/enquiry', headers={'origin': APEX}, json=ENQUIRY)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail'], enquiry_api.UNAVAILABLE)
        with patch.dict(os.environ, {'DATABASE_URL': ''}), self.assertLogs('uvicorn.error', 'ERROR'):
            self.assertEqual(self.client.post('/api/enquiry', headers={'origin': APEX}, json=ENQUIRY).status_code, 503)

    def test_startup_survives_unreachable_database(self):
        with self.assertLogs('uvicorn.error', 'ERROR'), TestClient(server.app) as client:
            self.assertEqual(client.get('/health').status_code, 200)

    def test_no_secret_in_any_public_response(self):
        origin = {'origin': APEX}
        with self.assertLogs('uvicorn.error', 'ERROR'):
            responses = [self.client.get(f'/{name}') for name in sorted(server.PUBLIC_FILES)] + [
                self.client.get('/'), self.client.get('/health'), self.client.get('/api/chat/status'),
                self.client.get('/.env'), self.client.get('/server.py'), self.client.get('/railway.toml'),
                self.client.post('/api/voice/token', headers=origin, json={'language': 'en-IN'}),
                self.client.post('/api/voice/token', json={}),
                self.client.post('/api/voice/token', headers=origin, json={'language': 'bad'}),
                self.client.post('/api/enquiry', headers=origin, json=ENQUIRY),
                self.client.post('/api/enquiry', headers=origin, json={**ENQUIRY, 'email': 'bad'}),
            ]
        for response in responses:
            exposed = response.text + ' '.join(f'{k}: {v}' for k, v in response.headers.items())
            for name, value in SECRETS.items():
                self.assertNotIn(value, exposed, f'{name} exposed by {response.request.method} {response.request.url.path}')
            self.assertNotIn('sentinel-db-password', exposed)

if __name__ == '__main__': unittest.main()
