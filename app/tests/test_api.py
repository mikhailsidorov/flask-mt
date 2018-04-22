import json
import unittest
from base64 import b64encode
from datetime import datetime, date, timedelta

from flask import url_for

from app import create_app, db
from app.models import User, Post
from config import Config


class APITestCase(unittest.TestCase):
    def setUp(self):
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
        self.user2.set_password(self.test_password)
        self.user2_token = self.user2.get_token()
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        self.basic_auth_headers = {
            'Authorization': 'Basic ' + b64encode(bytes("{0}:{1}".format(
                self.user1.username,
                self.test_password),
                'ascii')).decode('ascii')}
        self.user1_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user1_token}
        self.user_data = {
            'username': 'user100', 
            'password': self.test_password,
            'email': 'user100@example.com'}
        self.updated_user_data = {
            'username': 'user100',
            'email': 'user100@example.com',
            'about_me': 'blabla'}
        post1 = Post(body='test post 1', author=self.user1, language='en')
        post2 = Post(body='test post 2', author=self.user1, language='en')
        db.session.add_all([post1, post2])
        db.session.commit()

    def tearDown(self):
        db.session.close()
        # db.session.remove()
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

    def test_get_token_auth_required(self):
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

    def test_get_user(self):
        response = self.client.get(
            url_for('api.get_user', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = {
                'id': self.user1.id,
                'username': self.user1.username,
                'last_seen': self.user1.last_seen.isoformat() + 'Z',
                'about_me': self.user1.about_me,
                'post_count': self.user1.posts.count(),
                'follower_count': self.user1.followers.count(),
                'followed_count': self.user1.followed.count(),
                '_links': {
                    'self': url_for('api.get_user', id=self.user1.id),
                    'followers': url_for('api.get_followers', id=self.user1.id),
                    'followed': url_for('api.get_followed', id=self.user1.id),
                    'avatar': self.user1.avatar(128)
                }
            }
        self.assertEqual(data, data1)

    def test_get_user_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_user', id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_user', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.get_user', id=100),
            headers=self.user1_token_auth_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_get_users(self):
        response = self.client.get(
            url_for('api.get_users'),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(User.query, 1, 10, 'api.get_users')
        self.assertEqual(data, data1)
        self.assertEqual(data['_meta']['total_items'], 2)
        self.assertIn(self.user1.to_dict(), data['items'])
        self.assertIn(self.user2.to_dict(), data['items'])

    def test_get_users_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_users'), headers={})
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_users'),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_followers(self):
        # self.maxDiff = None
        response = self.client.get(
            url_for('api.get_followers', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(self.user1.followers, 1, 10, 'api.get_followers', id=self.user1.id)
        self.assertEqual(data, data1)

    def test_get_followers_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.get_followers', id=100),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followers_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followers', id=self.user1.id),
            headers={})
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
        data1 = User.to_collection_dict(self.user1.followed, 1, 10, 'api.get_followed', id=self.user1.id)
        self.assertEqual(data, data1)

    def test_get_followed_user_does_not_exist(self):
        response = self.client.get(
            url_for('api.get_followed', id=100),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followed_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followed', id=self.user1.id),
            headers={})
        self.assertEqual(response.status_code, 401)

    def test_create_user(self):
        response = self.client.post(
            url_for('api.create_user'),
            data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        new_user = User.query.filter_by(
            username=self.user_data['username']).first()
        self.assertEqual(
            response.headers['Location'],
            url_for('api.get_user', id=new_user.id, _external=True))
        data = json.loads(response.data)
        self.assertEqual(data['username'], self.user_data['username'])
        self.assertEqual(data['id'], new_user.id)
        self.assertTrue(new_user.check_password(self.user_data['password']))
        self.assertEqual(new_user.email, self.user_data['email'])

    def test_create_user_error_on_incomplete_data(self):
        user_data = self.user_data.copy()
        user_data.pop('email', None)
        error_text = 'must include username, email and password fields'
        response = self.client.post(
            url_for('api.create_user'), data=json.dumps(user_data))
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))

        user_data = self.user_data.copy()
        user_data.pop('password', None)
        response = self.client.post(
            url_for('api.create_user'), data=json.dumps(user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))

        user_data = self.user_data.copy()
        user_data.pop('username', None)
        response = self.client.post(
            url_for('api.create_user'), data=json.dumps(user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))

    def test_create_user_error_on_username_already_used(self):
        self.user_data['username'] = self.user1.username
        error_text = 'please use a different username'
        response = self.client.post(
            url_for('api.create_user'), data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))

    def test_create_user_error_on_email_already_used(self):
        self.user_data['email'] = self.user1.email
        error_text = 'please use a different email address'
        response = self.client.post(
            url_for('api.create_user'), data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))

    def test_update_user(self):
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(
            data['username'], self.updated_user_data['username'])
        self.assertEqual(
            data['about_me'], self.updated_user_data['about_me'])
        self.assertEqual(
            self.user1.email, self.updated_user_data['email'])

    def test_update_user_error_on_not_self_update(self):
        response = self.client.put(
            url_for('api.update_user', id=self.user2.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_on_user_name_already_used(self):
        error_text = 'please use a different username'
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'username': self.user2.username}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'username': 'user100'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_on_email_already_used(self):
        error_text = 'please use a different email address'
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'email': self.user2.email}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(error_text, str(response.data))
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'email': 'user100@example.com'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_token_auth_required(self):
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers={},
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)
        response = self.client.put(
            url_for('api.update_user', id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_user_posts(self):
        response = self.client.get(
            url_for('api.get_user_posts', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        posts_query = Post.query.filter_by(user_id=self.user1.id)
        data1 = User.to_collection_dict(
            posts_query, 1, 10, 'api.get_user_posts', id=self.user1.id)
        self.assertEqual(data, data1)
        self.assertEqual(data['_meta']['total_items'], 2)
        for post in self.user1.posts.all():
            self.assertIn(post.to_dict(), data['items'])

    def test_get_user_posts_error_on_user_does_not_exist(self):
        response = self.client.get(
            url_for('api.get_user_posts', id=1000),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_user_posts_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_user_posts', id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response  = self.client.get(
            url_for('api.get_user_posts', id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
