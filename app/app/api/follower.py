from flask import jsonify, request
from flask_restful import Resource

from app.api.auth import token_auth
from app.models import User


class FollowerList(Resource):
    method_decorators = {
        'get': [token_auth.login_required]
    }

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = User.to_collection_dict(user.followers, page, per_page,
                                       'api.follower_list', user_id=user_id)
        return jsonify(data)


class FollowedDetail(Resource):
    method_decorators = {
        'delete': [token_auth.login_required]
    }

    # Unfollow action
    def delete(self, user_id):
        pass


class FollowedList(Resource):
    method_decorators = {
        'get': [token_auth.login_required],
        'post': [token_auth.login_required],
        'delete': [token_auth.login_required]
    }

    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = User.to_collection_dict(user.followed, page, per_page,
                                       'api.followed_list', user_id=user_id)
        return jsonify(data)

    # Follow action
    def post(self, user_id):
        pass
