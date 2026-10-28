import json
from unittest.mock import patch,MagicMock
from django.test import TestCase,Client
from django.contrib.auth.models import User,Group
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document,Chunk,Chat
from .retrieval import retrieve
class SecurityTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user('alice',password='long-test-password')
  self.other=User.objects.create_user('bob',password='long-test-password')
  self.editor=User.objects.create_user('editor',password='long-test-password');self.editor.groups.add(Group.objects.create(name='editor'))
  self.admin=User.objects.create_superuser('admin',password='long-test-password')
  self.public=Document.objects.create(title='Public',body='Leave is requested ten days in advance.',access='all')
  self.secret=Document.objects.create(title='Board reserve',body='Confidential reserve 470000 PLN',access='admin')
  self.pc=Chunk.objects.create(document=self.public,position=0,text=self.public.body,vector=[1,0])
  self.sc=Chunk.objects.create(document=self.secret,position=0,text=self.secret.body,vector=[1,0])
  self.chat=Chat.objects.create(owner=self.user)
  self.client.force_login(self.user)
 def test_anonymous_denied(self):
  self.client.logout()
  for path in ['chats','documents',f'sources/{self.pc.pk}']:
   self.assertEqual(self.client.get('/api/v1/'+path).status_code,403)
 def test_chat_read_isolation(self):
  self.client.force_login(self.other);self.assertEqual(self.client.get(f'/api/v1/chats/{self.chat.pk}').status_code,404)
 def test_chat_delete_isolation(self):
  self.client.force_login(self.other);self.assertEqual(self.client.delete(f'/api/v1/chats/{self.chat.pk}').status_code,404);self.assertTrue(Chat.objects.filter(pk=self.chat.pk).exists())
 def test_chat_ask_isolation(self):
  self.client.force_login(self.other);self.assertEqual(self.client.post(f'/api/v1/chats/{self.chat.pk}/ask',{'text':'hello'},content_type='application/json').status_code,404)
 def test_document_acl(self):
  data=self.client.get('/api/v1/documents').json();self.assertEqual([d['title'] for d in data],['Public'])
 def test_source_acl(self):self.assertEqual(self.client.get(f'/api/v1/sources/{self.sc.pk}').status_code,404)
 @patch('desk.retrieval.encode',return_value=[[1,0]])
 def test_acl_before_vector_search(self,mock):self.assertEqual([s['id'] for s in retrieve(self.user,'reserve')],[self.pc.pk])
 def test_upload_user_denied(self):self.assertEqual(self.client.post('/api/v1/documents',{'file':SimpleUploadedFile('a.txt',b'a'*40)}).status_code,403)
 def test_editor_cannot_publish_admin(self):
  self.client.force_login(self.editor);self.assertEqual(self.client.post('/api/v1/documents',{'file':SimpleUploadedFile('a.txt',b'a'*40),'access':'admin'}).status_code,400)
 def test_invalid_uploads(self):
  self.client.force_login(self.editor)
  for name,body in [('a.exe',b'a'*40),('a.txt',b''),('a.txt',b'a'*(5*1024*1024+1)),('a.txt',b'\xff'*100)]:
   self.assertEqual(self.client.post('/api/v1/documents',{'file':SimpleUploadedFile(name,body)}).status_code,400)
 def test_csrf_login_required(self):
  c=Client(enforce_csrf_checks=True);self.assertEqual(c.post('/api/v1/login',{'username':'alice','password':'long-test-password'},content_type='application/json').status_code,403)
 def test_csrf_mutation_required(self):
  c=Client(enforce_csrf_checks=True);c.force_login(self.user);self.assertEqual(c.post('/api/v1/chats').status_code,403)
 def test_real_login_csrf_rotation(self):
  c=Client(enforce_csrf_checks=True);token=c.get('/api/v1/session').json()['csrf'];r=c.post('/api/v1/login',{'username':'alice','password':'long-test-password'},content_type='application/json',HTTP_X_CSRFTOKEN=token);self.assertEqual(r.status_code,200);self.assertNotEqual(token,r.json()['csrf'])
 def test_invalid_question(self):
  for query in ['', 'x'*2001,42]:self.assertEqual(self.client.post(f'/api/v1/chats/{self.chat.pk}/ask',{'text':query},content_type='application/json').status_code,400)
 @patch('desk.views.retrieve',return_value=[])
 def test_no_evidence_no_generation(self,mock):
  with patch('desk.views.requests.post') as post:
   r=self.client.post(f'/api/v1/chats/{self.chat.pk}/ask',{'text':'Mars?'},content_type='application/json');body=b''.join(r.streaming_content).decode();self.assertIn('done',body);post.assert_not_called()
 @patch('desk.views.retrieve')
 def test_invalid_citation_rejected(self,mock):
  mock.return_value=[{'id':self.pc.pk,'title':'Public','text':'Leave','document_id':self.public.pk}]
  response=MagicMock();response.__enter__.return_value=response;response.iter_lines.return_value=[json.dumps({'message':{'content':'Fabricated fact [99999]'},'done':True}).encode()]
  with patch('desk.views.requests.post',return_value=response):
   r=self.client.post(f'/api/v1/chats/{self.chat.pk}/ask',{'text':'Leave?'},content_type='application/json');body=b''.join(r.streaming_content).decode();self.assertNotIn('Fabricated fact',body)
 def test_request_id_header(self):self.assertEqual(len(self.client.get('/api/v1/health')['X-Request-ID']),32)
 @patch('desk.views.authenticate',return_value=None)
 def test_login_throttle(self,mock):
  for _ in range(10):self.assertEqual(self.client.post('/api/v1/login',{'username':'invalid','password':'invalid'},content_type='application/json',REMOTE_ADDR='203.0.113.99').status_code,401)
  self.assertEqual(self.client.post('/api/v1/login',{'username':'invalid','password':'invalid'},content_type='application/json',REMOTE_ADDR='203.0.113.99').status_code,429)
 def test_revoked_history_sources_hidden(self):
  from .models import Message
  Message.objects.create(chat=self.chat,role='assistant',text='Sensitive answer 470000',sources=[{'id':self.sc.pk,'title':'Secret','text':'470000'}])
  response=self.client.get(f'/api/v1/chats/{self.chat.pk}');self.assertNotIn('470000',response.content.decode())
 @patch('desk.views.retrieve')
 def test_truncated_generator_not_saved(self,mock):
  mock.return_value=[{'id':self.pc.pk,'title':'Public','text':'Leave','document_id':self.public.pk}]
  response=MagicMock();response.__enter__.return_value=response;response.iter_lines.return_value=[json.dumps({'message':{'content':f'Partial [{self.pc.pk}]'}}).encode()]
  with patch('desk.views.requests.post',return_value=response):
   r=self.client.post(f'/api/v1/chats/{self.chat.pk}/ask',{'text':'Leave?'},content_type='application/json');body=b''.join(r.streaming_content).decode();self.assertIn('error',body);self.assertFalse(self.chat.messages.filter(role='assistant').exists())
 @patch('desk.retrieval.encode',side_effect=RuntimeError('unavailable'))
 def test_readiness_unavailable(self,mock):self.assertEqual(self.client.get('/api/v1/readiness').status_code,503)
