from app import app
from app.models import Post


class PostSchema(app.marshmallow.ModelSchema):
    class Meta:
        model = Post
    _links = app.marshmallow.Hyperlinks({
        'self': app.marshmallow.URLFor('api.post_detail', id='<id>'),
        'author': app.marshmallow.URLFor('api.user_detail', user_id='user_id')
    })
