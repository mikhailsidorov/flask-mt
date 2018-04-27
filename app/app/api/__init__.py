from flask import Blueprint
from flask_restful import Api

bp = Blueprint('api', __name__)
api = Api(bp)

# from . import users, errors, tokens

from .follower import FollowedDetail, FollowedList, FollowerList
from .post import PostDetail, PostList
from .token import Token
from .user import UserDetail, UserList


api.add_resource(UserDetail, '/users/<int:user_id>', endpoint='user_detail')
api.add_resource(UserList, '/users', endpoint='user_list')
api.add_resource(Token, '/tokens', endpoint='tokens')
api.add_resource(PostList, '/users/<int:user_id>/posts', endpoint='post_list')
api.add_resource(PostDetail, '/users/<int:user_id>/posts/<int:post_id>',
                 endpoint='post_detail')
api.add_resource(FollowerList, '/users/<int:user_id>/followers',
                 endpoint='follower_list')
api.add_resource(FollowedList, '/users/<int:user_id>/followed',
                 endpoint='followed_list')
api.add_resource(FollowedDetail,
                 '/users/<int:user_id>/followed/<int:followed_id>',
                 endpoint='followed_detail')
