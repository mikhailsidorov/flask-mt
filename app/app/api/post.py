from flask import jsonify, request, url_for
from flask_restful import Resource

from app import db
from .auth import token_auth
from .permissions import CanCreatePost, CanUpdatePost, CanDeletePost, allows
from app.models import Post, User
from .errors.exceptions import PostRequiredFieldsIsMissing
from .schemas import PostSchema


class PostDetail(Resource):
    post_schema = PostSchema()

    method_decorators = {
        'get': [token_auth.login_required],
        'put': [allows.requires(CanUpdatePost()), token_auth.login_required],
        'delete': [allows.requires(CanDeletePost()), token_auth.login_required]
    }

    def get(self, user_id, post_id):
        post = Post.query.get_or_404(post_id)
        return self.post_schema.jsonify(post)

    def put(self, user_id, post_id):
        post = Post.query.get_or_404(post_id)
        data = request.get_json() or {}
        if 'body' not in data or data['body'] == '':
            raise PostRequiredFieldsIsMissing
        post.from_dict(data)
        db.session.commit()
        response = self.post_schema.jsonify(post)
        response.status_code = 204
        return response

    def delete(self, user_id, post_id):
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        return '', 200


class PostList(Resource):
    method_decorators = {
        'get': [token_auth.login_required],
        'post': [allows.requires(CanCreatePost()), token_auth.login_required]
    }

    def get(self, user_id):
        User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        posts_query = Post.query.filter_by(user_id=user_id)
        data = User.to_collection_dict(posts_query, page, per_page,
                                       'api.post_list', user_id=user_id)
        return jsonify(data)

    def post(self, user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}
        if 'body' not in data or 'user_id' not in data:
            raise PostRequiredFieldsIsMissing
        post = Post()
        post.from_dict(data)
        db.session.add(post)
        db.session.commit()
        response = jsonify(post.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for(
            'api.post_detail', user_id=user.id, post_id=post.id)
        return response
