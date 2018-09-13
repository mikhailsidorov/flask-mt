from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

from . import exceptions


def error_response(error):
    payload = {'error': HTTP_STATUS_CODES.get(error.status_code,
               'Unknown error')}
    if error.description:
        payload['message'] = error.description
    response = jsonify(payload)
    response.status_code = error.status_code
    return response
