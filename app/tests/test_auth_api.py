import json
import unittest
from base64 import b64encode
from datetime import datetime

from app import create_app, db
from app.models import User
from config import Config


class AuthAPITestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.app = create_app(Config)
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1 = User(username='john', email='john@example.com')
        self.test_password = 'test_password'
        self.user1.set_password(self.test_password)
        self.user1_token = self.user1.get_token()
        db.session.add(self.user1)
        db.session.commit()
        self.basic_auth_headers = {
            'Authorization': 'Basic ' + b64encode(bytes("{0}:{1}".format(
                self.user1.username,
                self.test_password),
                'ascii')).decode('ascii')}
        self.user1_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user1_token}

    def tearDown(self):
        db.session.close()
        db.drop_all()
        self.app_context.pop()

    def test_get_token(self):
        response = self.client.post(
            '/api/tokens', headers=self.basic_auth_headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['token'], self.user1_token)
        self.assertEqual(data['user_id'], self.user1.id)
        expiration_date = datetime.strptime(
            data['token_expiration'], '%a, %d %b %Y %X %Z')
        self.assertGreater(expiration_date, datetime.now())

    def test_get_token_basic_auth_required(self):
        response = self.client.post('/api/tokens')
        self.assertEqual(response.status_code, 401)
        response = self.client.post(
            '/api/tokens', headers=self.basic_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_revoke_token(self):
        response = self.client.delete(
            '/api/tokens', headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 204)

    def test_revoke_token_auth_required(self):
        response = self.client.delete('/api/tokens')
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(
            '/api/tokens', headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 204)
