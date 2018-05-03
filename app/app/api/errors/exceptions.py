from werkzeug.exceptions import BadRequest


class PostRequiredFieldsIsMissing(BadRequest):
    description = 'must include post_body and user_id fields'


class UserIdFieldIsMissing(BadRequest):
    description = 'must include user_id field'


class UsernameAlreadyUsed(BadRequest):
    description = 'please use a different username'


class EmailAddressAlreadyUsed(BadRequest):
    description = 'please use a different email address'


class UserRequiredFiesldsIsMissing(BadRequest):
    description = 'must include username, email and password fields'
