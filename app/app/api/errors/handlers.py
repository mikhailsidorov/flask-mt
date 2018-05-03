from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

from . import exceptions
from .. import bp


def error_response(error):
    payload = {'error': HTTP_STATUS_CODES.get(error.status_code,
               'Unknown error')}
    if error.description:
        payload['message'] = error.description
    response = jsonify(payload)
    response.status_code = error.status_code
    return response


bp.register_error_handler(exceptions.PostRequiredFieldsMissed, error_response)
bp.register_error_handler(exceptions.UsernameAlreadyUsed, error_response)
bp.register_error_handler(exceptions.EmailAddressAlreadyUsed, error_response)
bp.register_error_handler(exceptions.UserRequiredFiesldsMissed, error_response)
bp.register_error_handler(exceptions.UserIdFieldIsMissing, error_response)
