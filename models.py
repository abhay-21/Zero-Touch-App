from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─── Association Tables ──────────────────────────────────────────
community_members = db.Table('community_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('community_id', db.Integer, db.ForeignKey('community.id'))
)

followers_table = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# ─── Models ──────────────────────────────────────────────────────
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), nullable=True, default='')
    avatar_seed = db.Column(db.String(80), nullable=True)
    upi_id = db.Column(db.String(100), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    karma = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', foreign_keys='Post.user_id')
    boards = db.relationship('Board', backref='owner', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic', foreign_keys='Notification.user_id')
    followed = db.relationship('User', secondary=followers_table,
                               primaryjoin=(followers_table.c.follower_id == id),
                               secondaryjoin=(followers_table.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_url(self):
        seed = self.avatar_seed or self.username
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={seed}"

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.followed.count()

    def __repr__(self):
        return f'<User {self.username}>'


class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(400), nullable=True)
    emoji = db.Column(db.String(10), default='🌐')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    members = db.relationship('User', secondary=community_members, backref='communities', lazy='dynamic')
    posts = db.relationship('Post', backref='community', lazy='dynamic')

    @property
    def member_count(self):
        return self.members.count()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)  # YouTube embed link
    post_type = db.Column(db.String(20), default='text')  # text, image, video, reel
    tags = db.Column(db.String(300), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=True)
    
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def score(self):
        # Simple hotness score: likes + recency boost
        age_hours = max(1, (datetime.utcnow() - self.timestamp).total_seconds() / 3600)
        return round(self.like_count / (age_hours ** 1.5), 4)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.relationship('User', backref='comments')


class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), default='📌')
    description = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pins = db.relationship('Pin', backref='board', lazy='dynamic', cascade='all, delete-orphan')


class Pin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    pinned_at = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship('Post')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.String(300), nullable=False)
    link = db.Column(db.String(200), nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actor = db.relationship('User', foreign_keys=[actor_id])
