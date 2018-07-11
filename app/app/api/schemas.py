from marshmallow import fields

from app.models import Post
from app import marshmallow as ma


class IsoDateTimeField(fields.DateTime):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return value.isoformat() + 'Z'


class PostSchema(ma.ModelSchema):
    class Meta:
        model = Post
        include_fk = True
        exclude = ('author',)

    timestamp = IsoDateTimeField(dump_only=True)
    _links = ma.Hyperlinks({
        'self': ma.URLFor('api.post_detail', post_id='<id>',
                          user_id='<user_id>'),
        'author': ma.URLFor('api.user_detail', user_id='<user_id>')
    })
