
import unittest
from datetime import datetime, timedelta

from flask import url_for

from app import create_app, db
from app.models import User, Post
from config import Config


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.utcnow()
        p1 = Post(body='Post form john', author=u1, timestamp=now + timedelta(seconds=1))
        p2 = Post(body='Post form susan', author=u2, timestamp=now + timedelta(seconds=4))
        p3 = Post(body='Post from mary', author=u3, timestamp=now + timedelta(seconds=3))
        p4 = Post(body='Post from david', author=u4, timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()

        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

    def test_(self):
        self.user1 = User(username='john', email='john@example.com')
        db.session.add(self.user1)
        db.session.commit()
        data = {
            'id': self.user1.id,
            'username': self.user1.username,
            'last_seen': self.user1.last_seen.isoformat() + 'Z',
            'about_me': self.user1.about_me,
            'post_count': self.user1.posts.count(),
            'follower_count': self.user1.followers.count(),
            'followed_count': self.user1.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.user1.id),
                'followers': url_for('api.get_followers', id=self.user1.id),
                'followed': url_for('api.get_followed', id=self.user1.id),
                'avatar': self.user1.avatar(128)
            }
        }
        data1 = User.query.get_or_404(self.user1.id).to_dict()
        self.assertEqual(data, data1)
