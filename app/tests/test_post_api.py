import json
from pprint import pprint
import unittest

from flask_restful import url_for

from app import create_app, db
from app.models import User, Post
from config import Config
from app.api.errors import exceptions


class PostAPITestCase(unittest.TestCase):
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
        self.user2.set_password(self.test_password)
        self.user2_token = self.user2.get_token()
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        self.user1_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user1_token}
        self.post_data1 = {'body': 'Test message', 'user_id': self.user1.id,
                           'language': 'en-EN'}
        self.post_data2 = {'body': 'Test message', 'user_id': self.user2.id,
                           'language': 'en-EN'}
        self.updated_post1_data = {'body': 'Updated message',
                                   'user_id': self.user1.id,
                                   'language': 'en-EN'}
        self.post1 = Post(body='user1 test post 1', author=self.user1,
                          language='en')

        self.post2 = Post(body='user1 test post 2', author=self.user1,
                          language='en')
        self.post1_user2 = Post(body='user2 test post', author=self.user2,
                                language='en')
        db.session.add_all([self.post1, self.post2])
        db.session.commit()

    def tearDown(self):
        db.session.close()
        db.drop_all()
        self.app_context.pop()

    def test_get_user_posts(self):
        response = self.client.get(
            url_for('api.post_list', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        posts_query = Post.query.filter_by(user_id=self.user1.id)
        data1 = User.to_collection_dict(
            posts_query, 1, 10, 'api.post_list', user_id=self.user1.id)
        self.assertEqual(data, data1)
        self.assertEqual(data['_meta']['total_items'], 2)
        for post in self.user1.posts.all():
            self.assertIn(post.to_dict(), data['items'])

    def test_get_user_posts_error_on_user_does_not_exist(self):
        response = self.client.get(
            url_for('api.post_list', user_id=1000),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_user_posts_token_auth_required(self):
        response = self.client.get(
            url_for('api.post_list', user_id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.post_list', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_create_user_post(self):
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps(self.post_data1),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        data1 = json.loads(response.data)
        data2 = Post.query.get(data1['id']).to_dict()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data1, data2)
        self.assertEqual(
            response.headers['Location'],
            url_for('api.post_detail',
                    user_id=self.user1.id,
                    post_id=data1['id'],
                    _external=True))

    def test_create_user_post_error_on_empty_data_request(self):
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps({}),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.UserIdFieldIsMissing.description,
                      str(response.data))
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps({'user_id': self.user1.id}),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.PostRequiredFieldsIsMissing.description,
                      str(response.data))

    def test_create_user_post_error_on_not_own_post_creation(self):
        response = self.client.post(
            url_for('api.post_list', user_id=self.user2.id),
            data=json.dumps(self.post_data2),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps(self.post_data1),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_create_user_post_error_on_not_equal_user_id_in_post_data(self):
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps(self.post_data2),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            url_for('api.post_list', user_id=self.user1.id),
            data=json.dumps(self.post_data1),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_create_user_post_token_auth_required(self):
        response = self.client.get(
            url_for('api.post_list', user_id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.post_list', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_user_post_get_own_post(self):
        response = self.client.get(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.post1.to_dict())

    def test_get_user_post_get_not_own_post(self):
        response = self.client.get(
            url_for('api.post_detail', user_id=self.user2.id,
                    post_id=self.post2.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.post2.to_dict())

    def test_get_user_post_token_auth_required(self):
        response = self.client.get(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            data=json.dumps(self.updated_post1_data),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_update_post_error_on_not_equal_user_id_in_post_data(self):
        post_data = self.updated_post1_data.copy()
        post_data['user_id'] = self.user2.id
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            data=json.dumps(post_data),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_update_post_error_on_post_does_not_exists(self):
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=1000),
            data=json.dumps(self.post_data1),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_update_post_token_auth_required(self):
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            data=json.dumps(self.post_data1),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_update_post_error_on_user_does_not_exists(self):
        """Works same as in case token auth required and updating
        not own post.
        """

    def test_update_post_error_on_empty_data_request(self):
        post_data = self.updated_post1_data.copy()
        post_data.pop('body')
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user1.id,
                    post_id=self.post1.id),
            data=json.dumps(post_data),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_post_error_on_update_not_own_post(self):
        response = self.client.put(
            url_for('api.post_detail', user_id=self.user2.id,
                    post_id=self.post1_user2.id),
            data=json.dumps(self.post_data2),
            headers=self.user1_token_auth_headers,
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
