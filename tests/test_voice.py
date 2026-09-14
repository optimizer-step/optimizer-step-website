import os
import unittest
from unittest.mock import patch
import jwt
from fastapi.testclient import TestClient
import server

class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        server.attempts.clear()
        self.headers = {'origin': 'http://localhost:8000'}
        self.env = patch.dict(os.environ, {
            'LIVEKIT_URL': 'wss://test.livekit.cloud', 'LIVEKIT_API_KEY': 'test',
            'LIVEKIT_API_SECRET': 'x' * 40, 'SARVAM_API_KEY': 'test',
            'VOICE_ALLOWED_ORIGIN': 'http://localhost:8000'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_token_scope_and_dispatch(self):
        result = self.client.post('/api/voice/token', headers=self.headers, json={'language':'te-IN'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers['cache-control'], 'no-store')
        data = jwt.decode(result.json()['participant_token'], 'x' * 40, algorithms=['HS256'])
        self.assertTrue(data['video']['roomJoin'])
        self.assertEqual(data['video']['canPublishSources'], ['microphone'])
        self.assertEqual(data['roomConfig']['agents'][0]['agentName'], 'optimizer-voice')
        self.assertLessEqual(data['exp'] - data['nbf'], 60)

    def test_validation_and_limits(self):
        self.assertEqual(self.client.post('/api/voice/token', json={}).status_code, 403)
        self.assertEqual(self.client.post('/api/voice/token', headers=self.headers, json={'language':'bad'}).status_code, 422)
        self.assertEqual(self.client.post('/api/voice/token', headers=self.headers, json={'name':'x'*81}).status_code, 422)
        for _ in range(3):
            self.assertEqual(self.client.post('/api/voice/token', headers=self.headers, json={}).status_code, 200)
        self.assertEqual(self.client.post('/api/voice/token', headers=self.headers, json={}).status_code, 429)

    def test_missing_configuration_and_private_files(self):
        with patch.dict(os.environ, {'SARVAM_API_KEY':''}):
            self.assertEqual(self.client.post('/api/voice/token', headers=self.headers, json={}).status_code, 503)
        for path in ['/.env', '/agent.py', '/requirements.txt', '/.git/config']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/').status_code, 200)

if __name__ == '__main__':
    unittest.main()
