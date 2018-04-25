import json
import unittest

from flask import url_for

from app import create_app, db
from app.models import User
from config import Config


class UserAPITestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.app = create_app(Config)
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1 = User(username='john', email='john@example.com')
        self.user2 = User(username='Siri', email='siri@example.com')
        self.test_password = 'test_password'
        self.user1.set_password(self.test_password)
        self.user1_token = self.user1.get_token()
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        self.user1_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user1_token}

    def tearDown(self):
        db.session.close()
        db.drop_all()
        self.app_context.pop()

    def test_get_followers(self):
        response = self.client.get(
            url_for('api.get_followers', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(
            self.user1.followers, 1, 10, 'api.get_followers',
            id=self.user1.id)
        self.assertEqual(data, data1)

    def test_get_followers_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.get_followers', id=100),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followers_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followers', id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_followers', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_followed(self):
        response = self.client.get(
            url_for('api.get_followed', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(
            self.user1.followed, 1, 10, 'api.get_followed', id=self.user1.id)
        self.assertEqual(data, data1)

    def test_get_followed_user_does_not_exist(self):
        response = self.client.get(
            url_for('api.get_followed', id=100),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followed_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followed', id=self.user1.id))
        self.assertEqual(response.status_code, 401)
