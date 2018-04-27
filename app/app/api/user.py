from flask import jsonify, request, url_for
from flask_restful import Resource

from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request, invalid_post_data
from app.models import User
from app.authr import allows, CanUpdateProfile, CanDeleteProfile


class UserDetail(Resource):
    method_decorators = {
        'get': [token_auth.login_required],
        'put': [allows.requires(CanUpdateProfile()),
                token_auth.login_required],
        'delete': [allows.requires(CanDeleteProfile()),
                   token_auth.login_required]
    }

    def get(self, user_id):
        return jsonify(User.query.get_or_404(user_id).to_dict())

    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}
        if 'username' in data and data['username'] != user.username and \
                User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
        if 'email' in data and data['email'] != user.email and \
                User.query.filter_by(email=data['email']).first():
            return bad_request('please use a different email address')
        user.from_dict(data, new_user=False)
        db.session.commit()
        return jsonify(user.to_dict())

    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return ('', 200)


class UserList(Resource):
    method_decorators = {
        'get': [token_auth.login_required],
    }

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = User.to_collection_dict(
            User.query, page, per_page, 'api.user_list')
        return jsonify(data)

    def post(self):
        data = request.get_json() or {}
        if not is_valid_data(data):
            return invalid_post_data()
        if User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
        if User.query.filter_by(email=data['email']).first():
            return bad_request('please use a different email address')
        user = User()
        user.from_dict(data, new_user=True)
        db.session.add(user)
        db.session.commit()
        response = jsonify(user.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for('api.user_detail',
                                               user_id=user.id)
        return response


def is_valid_data(data):
    return not ('username' not in data or
                'email' not in data or
                'password' not in data)
