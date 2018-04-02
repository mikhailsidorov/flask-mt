from flask_allows import Allows, Requirement
from flask import g


allows = Allows(identity_loader=lambda: g.current_user)


class CanUpdateProfile(Requirement):
    def fulfill(self, identity, request):
        return self.is_profile_owner(identity, request)

    def is_profile_owner(self, identity, request):
        return identity.id == request.view_args['id']
