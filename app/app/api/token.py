from flask import g, jsonify
from flask_restful import Resource

from app import db
from app.api.auth import basic_auth, token_auth


class Token(Resource):
    method_decorators = {
        'post': [basic_auth.login_required],
        'delete': [token_auth.login_required]
    }

    def post(self):
        token = g.current_user.get_token()
        expiration = g.current_user.token_expiration
        db.session.commit()
        return jsonify({'token': token,
                        'user_id': g.current_user.id,
                        'token_expiration': expiration})

    def delete(self):
        g.current_user.revoke_token()
        db.session.commit()
        return '', 204
