"""
MongoDB models using mongoengine
These models will be stored in MongoDB while Django ORM models remain in SQLite/PostgreSQL
"""
from mongoengine import Document, StringField, DateTimeField, IntField, ListField, ReferenceField
from datetime import datetime

class UserProfile(Document):
    """User profile stored in MongoDB"""
    user_id = StringField(required=True, unique=True)  # Link to Django User
    bio = StringField(max_length=500)
    interests = ListField(StringField())
    profile_picture_url = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_profiles',
        'indexes': ['user_id']
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class Post(Document):
    """Blog post stored in MongoDB"""
    title = StringField(required=True, max_length=200)
    content = StringField(required=True)
    author_id = StringField(required=True)  # Link to Django User
    tags = ListField(StringField())
    likes_count = IntField(default=0)
    liked_by = ListField(StringField())  # List of user IDs who liked the post
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'posts',
        'indexes': [
            'author_id',
            '-created_at',
            'tags'
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class Comment(Document):
    """Comment on a post stored in MongoDB"""
    post_id = StringField(required=True)  # Link to Post
    author_id = StringField(required=True)  # Link to Django User
    content = StringField(required=True, max_length=1000)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'comments',
        'indexes': [
            'post_id',
            'author_id',
            '-created_at'
        ]
    }
