from flask import jsonify, request, url_for
from flask_restful import Resource

from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.authr import CanCreatePost, allows
from app.models import Post, User


class PostDetail(Resource):
    method_decorators = {
        'get': [token_auth.login_required],
    }

    def get(self, user_id, post_id):
        return jsonify(Post.query.get_or_404(post_id).to_dict())


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
            return bad_request('must include post_body field')
        post = Post()
        post.from_dict(data)
        db.session.add(post)
        db.session.commit()
        response = jsonify(post.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for(
            'api.post_detail', user_id=user.id, post_id=post.id)
        return response
