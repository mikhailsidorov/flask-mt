import json
import unittest

from flask_restful import url_for

from app import create_app, db
from app.models import User
from config import Config
from app.api.errors import exceptions


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
        self.user2.set_password(self.test_password)
        self.user2_token = self.user2.get_token()
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        self.user1_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user1_token}
        self.user2_token_auth_headers = {
            'Authorization': 'Bearer ' + self.user2_token}
        self.user_data = {'username': 'user100',
                          'password': self.test_password,
                          'email': 'user100@example.com'}
        self.updated_user_data = {'username': 'user100',
                                  'email': 'user100@example.com',
                                  'about_me': 'blabla'}

    def tearDown(self):
        db.session.close()
        db.drop_all()
        self.app_context.pop()

    def test_get_user(self):
        response = self.client.get(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = User.query.get(self.user1.id).to_dict()
        self.assertEqual(json.loads(response.data), data)

    def test_get_user_token_auth_required(self):
        response = self.client.get(
            url_for('api.user_detail', user_id=self.user1.id))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_user_does_not_exists(self):
        response = self.client.get(
            url_for('api.user_detail', user_id=100),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_users(self):
        response = self.client.get(
            url_for('api.user_list'), headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        data1 = User.to_collection_dict(User.query, 1, 10, 'api.user_list')
        self.assertEqual(data, data1)
        self.assertEqual(data['_meta']['total_items'], 2)
        self.assertIn(self.user1.to_dict(), data['items'])
        self.assertIn(self.user2.to_dict(), data['items'])

    def test_get_users_token_auth_required(self):
        response = self.client.get(url_for('api.user_list'), headers={})
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            url_for('api.user_list'), headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        response = self.client.post(
            url_for('api.user_list'),
            data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        new_user = User.query.filter_by(
            username=self.user_data['username']).first()
        self.assertEqual(
            response.headers['Location'],
            url_for('api.user_detail', user_id=new_user.id, _external=True))
        data = json.loads(response.data)
        self.assertEqual(data['username'], self.user_data['username'])
        self.assertEqual(data['id'], new_user.id)
        self.assertTrue(new_user.check_password(self.user_data['password']))
        self.assertEqual(new_user.email, self.user_data['email'])

    def test_create_user_error_on_incomplete_data(self):
        for key in self.user_data.keys():
            user_data = self.user_data.copy()
            user_data.pop(key, None)
            response = self.client.post(
                url_for('api.user_list'), data=json.dumps(user_data),
                content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertIn(exceptions.UserRequiredFiesldsIsMissing.description,
                          str(response.data))

    def test_create_user_error_on_username_already_used(self):
        self.user_data['username'] = self.user1.username
        response = self.client.post(
            url_for('api.user_list'), data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.UsernameAlreadyUsed.description,
                      str(response.data))

    def test_create_user_error_on_email_already_used(self):
        self.user_data['email'] = self.user1.email
        response = self.client.post(
            url_for('api.user_list'), data=json.dumps(self.user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.EmailAddressAlreadyUsed.description,
                      str(response.data))

    def test_update_user(self):
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
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
            url_for('api.user_detail', user_id=self.user2.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_on_user_name_already_used(self):
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'username': self.user2.username}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.UsernameAlreadyUsed.description,
                      str(response.data))
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'username': 'user100'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_on_email_already_used(self):
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'email': self.user2.email}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(exceptions.EmailAddressAlreadyUsed.description,
                      str(response.data))
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps({'email': 'user100@example.com'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_user_token_auth_required(self):
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers={},
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)
        response = self.client.put(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers,
            data=json.dumps(self.updated_user_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_delete_user(self):
        response = self.client.delete(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            url_for('api.user_detail', user_id=self.user1.id),
            headers=self.user2_token_auth_headers)
        self.assertEqual(response.status_code, 404)

    def tets_delete_error_on_not_self_deletion(self):
        response = self.client.delete(
            url_for('api.user_detail', user_id=self.user2.id),
            headers=self.user1_token_auth_headers)
        self.assertEqual(response.status_code, 401)

    def test_delete_user_token_auth_required(self):
        response = self.client.delete(
            url_for('api.user_detail', user_id=self.user1.id))
        self.assertEqual(response.status_code, 401)
