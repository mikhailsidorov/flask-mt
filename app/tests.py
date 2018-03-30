import json
import unittest
from base64 import b64encode
from datetime import datetime, date, timedelta

from flask import jsonify, url_for

from app import create_app, db
from app.models import User, Post
from config import Config


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.utcnow()
        p1 = Post(body='Post form john', author=u1, timestamp=now + timedelta(seconds=1))
        p2 = Post(body='Post form susan', author=u2, timestamp=now + timedelta(seconds=4))
        p3 = Post(body='Post from mary', author=u3, timestamp=now + timedelta(seconds=3))
        p4 = Post(body='Post from david', author=u4, timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()

        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        db.create_all()

        self.client = self.app.test_client()

        self.user = User(username='john', email='john@example.com')
        self.user2 = User(username='Siri', email='siri@example.com')
        db.session.add(self.user, self.user2)
        
        
        self.test_password = 'test_password'
        self.user.set_password(self.test_password)
        db.session.commit()
        self.token = self.user.get_token()

        self.user2.set_password(self.test_password)
        self.token2 = self.user2.get_token()
        
        self.basic_auth_headers = {
            'Authorization': 'Basic ' + b64encode(bytes("{0}:{1}".format(
                self.user.username,
                self.test_password),
                'ascii')).decode('ascii')
        }
        self.token_auth_headers = {
            'Authorization': 'Bearer ' + self.token
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_token(self):
        response = self.client.post(
            '/api/tokens', headers=self.basic_auth_headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['token'], self.token)
        self.assertEqual(data['user_id'], self.user.id)
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
            '/api/tokens', headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 204)
        print(response.data)

    def test_revoke_token_auth_required(self):
        response = self.client.delete('/api/tokens')
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(
            '/api/tokens', headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 204)

    def test_get_user(self):
        response = self.client.get(
            url_for('api.get_user', id=self.user.id),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = {
                'id': self.user.id,
                'username': self.user.username,
                'last_seen': self.user.last_seen.isoformat() + 'Z',
                'about_me': self.user.about_me,
                'post_count': self.user.posts.count(),
                'follower_count': self.user.followers.count(),
                'followed_count': self.user.followed.count(),
                '_links': {
                    'self': url_for('api.get_user', id=self.user.id),
                    'followers': url_for('api.get_followers', id=self.user.id),
                    'followed': url_for('api.get_followed', id=self.user.id),
                    'avatar': self.user.avatar(128)
                }
            }
        self.assertEqual(data, data1)

    def test_get_user_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_user', id=self.user.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_user', id=self.user.id),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.get_user', id=100),
            headers=self.token_auth_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_get_users(self):
        response = self.client.get(
            url_for('api.get_users'),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(User.query, 1, 10, 'api.get_users')
        self.assertEqual(data, data1)
        self.assertEqual(data['_meta']['total_items'], 2)
        self.assertIn(self.user.to_dict(), data['items'])
        self.assertIn(self.user2.to_dict(), data['items'])

    def test_get_users_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_users'), headers={})
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_users'),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_followers(self):
        # self.maxDiff = None
        response = self.client.get(
            url_for('api.get_followers', id=self.user.id),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(self.user.followers, 1, 10, 'api.get_followers', id=self.user.id)
        self.assertEqual(data, data1)

    def test_get_followers_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.get_followers', id=100),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followers_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followers', id=self.user.id),
            headers={})
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.get_followers', id=self.user.id),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_followed(self):
        response = self.client.get(
            url_for('api.get_followed', id=self.user.id),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(self.user.followed, 1, 10, 'api.get_followed', id=self.user.id)
        self.assertEqual(data, data1)

    def test_get_followed_user_does_not_exist(self):
        response = self.client.get(
            url_for('api.get_followed', id=100),
            headers=self.token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_followed_token_auth_required(self):
        response = self.client.get(
            url_for('api.get_followed', id=self.user.id),
            headers={})
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
