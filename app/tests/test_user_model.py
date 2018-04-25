
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
        self.user1 = User(username='john', email='john@example.com')
        self.user2 = User(username='susan', email='susan@example.com')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        self.user1.set_password('cat')
        self.assertFalse(self.user1.check_password('dog'))
        self.assertTrue(self.user1.check_password('cat'))

    def test_avatar(self):
        base_url = 'https://www.gravatar.com/avatar/'
        self.assertEqual(
            self.user1.avatar(128),
            (base_url+'d4c74594d841139328695756648b6bd6?d=identicon&s=128'))

    def test_follow(self):
        self.assertEqual(self.user1.followed.all(), [])
        self.assertEqual(self.user2.followers.all(), [])
        self.user1.follow(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertEqual(self.user1.followed.count(), 1)
        self.assertEqual(self.user2.followers.count(), 1)
        self.assertEqual(self.user2.followers.first().username, 'john')
        self.user1.unfollow(self.user2)
        db.session.commit()
        self.assertFalse(self.user1.is_following(self.user2))
        self.assertEqual(self.user1.followed.count(), 0)
        self.assertEqual(self.user2.followers.count(), 0)

    def test_follow_posts(self):
        now = datetime.utcnow()
        p1 = Post(
            body='Post from john', author=self.user1,
            timestamp=now + timedelta(seconds=1))
        p2 = Post(
            body='Post from susan', author=self.user2,
            timestamp=now + timedelta(seconds=4))
        db.session.add_all([p1, p2])
        db.session.commit()
        self.user1.follow(self.user2)
        self.user2.follow(self.user1)
        db.session.commit()
        posts1 = self.user1.followed_posts().all()
        posts2 = self.user2.followed_posts().all()
        self.assertEqual(posts1, [p2, p1])
        self.assertEqual(posts2, [p2, p1])

    def test_user_to_dict(self):
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
