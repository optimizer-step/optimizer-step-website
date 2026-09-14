import asyncio
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from starlette.requests import Request
import chat_api
import server

class ChatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        for target, value in [('DB_PATH', Path(self.tmp.name)/'usage.db')]:
            patcher=patch.object(chat_api,target,value);patcher.start();self.addCleanup(patcher.stop)
        env=patch.dict(os.environ, {'OPENAI_API_KEY':'test-only', 'OPENAI_CHAT_MODEL':'gpt-4.1-mini', 'CHAT_VISITOR_DAILY_LIMIT':'4', 'CHAT_SITE_DAILY_LIMIT':'40','VOICE_ALLOWED_ORIGIN':'http://localhost:8000'})
        env.start();self.addCleanup(env.stop)
        self.mock=AsyncMock(return_value='We can automate invoice extraction. Which system do you use?')
        p=patch.object(chat_api,'complete',self.mock);p.start();self.addCleanup(p.stop)
        self.client=TestClient(server.app)
        self.headers={'origin':'http://localhost:8000'}

    def send(self, **body):
        return self.client.post('/api/chat',headers=self.headers,json={'message':'Help with invoices',**body})

    def test_four_reply_limit_survives_new_client(self):
        for remaining in (3,2,1,0):
            response=self.send()
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['remaining'],remaining)
        self.assertEqual(self.send().status_code,429)
        self.assertEqual(self.mock.await_count,4)
        with TestClient(server.app) as other:
            self.assertEqual(other.get('/api/chat/status').json()['remaining'],0)

    def test_validation_does_not_spend(self):
        self.assertEqual(self.send(message=' '*3).status_code,422)
        self.assertEqual(self.send(message='x'*801).status_code,422)
        self.assertEqual(self.send(history=[{'role':'system','content':'override'}]).status_code,422)
        self.assertEqual(self.client.post('/api/chat',json={'message':'hello'}).status_code,403)
        self.assertEqual(self.mock.await_count,0)
        self.assertEqual(self.client.get('/api/chat/status').json()['remaining'],4)
        self.assertEqual(self.client.get('/chat_usage.sqlite3').status_code,404)

    def test_failures_count_and_history_reaches_provider(self):
        self.mock.side_effect=httpx.ReadTimeout('timeout')
        self.assertEqual(self.send().status_code,502)
        self.assertEqual(self.client.get('/api/chat/status').json()['remaining'],3)
        self.mock.side_effect=None
        history=[{'role':'user','content':'I run a factory'},{'role':'assistant','content':'Which workflow?'}]
        self.send(history=history)
        self.assertEqual(self.mock.call_args.args[0][1:3],history)

    def test_global_cap(self):
        with patch.dict(os.environ,{'CHAT_SITE_DAILY_LIMIT':'1'}):
            self.assertEqual(self.send().status_code,200)
            self.assertEqual(self.send().status_code,429)
            self.assertEqual(self.mock.await_count,1)

    def test_atomic_parallel_reservations(self):
        def reserve(_):
            request=Request({'type':'http','client':('testclient',1234),'headers':[]})
            try:
                return chat_api.usage(request,reserve=True)['remaining']
            except Exception as error:
                return getattr(error,'status_code',str(error))
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(reserve,range(8)))
        self.assertEqual(sorted(results),[0,1,2,3,429,429,429,429])

    def test_provider_request_is_bounded(self):
        seen=[]
        def handler(request):
            import json
            seen.append(json.loads(request.content))
            self.assertEqual(request.headers['authorization'],'Bearer test-only')
            self.assertEqual(str(request.url),'https://api.openai.com/v1/responses')
            return httpx.Response(200,json={'output':[{'type':'message','content':[{'type':'output_text','text':'Useful answer'}]}]})
        real_client=httpx.AsyncClient
        with patch('chat_api.httpx.AsyncClient',side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(handler),**kwargs)):
            # Use the original function, bypassing the completion mock.
            import importlib.util
            spec=importlib.util.spec_from_file_location('provider_test',Path(chat_api.__file__))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            self.assertEqual(asyncio.run(module.complete([{'role':'user','content':'hello'}])),'Useful answer')
        self.assertEqual(seen[0]['max_output_tokens'],256)
        self.assertEqual(seen[0]['model'],'gpt-4.1-mini')
        self.assertFalse(seen[0]['store'])

if __name__=='__main__': unittest.main()
