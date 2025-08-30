"""
Utility functions for MongoDB operations
"""
from .mongo_models import UserProfile, Post, Comment
from django.contrib.auth.models import User
from mongoengine.queryset.visitor import Q
from mongoengine.connection import get_db
import logging

logger = logging.getLogger(__name__)

def _check_mongodb_connection():
    """Check if MongoDB connection is available with caching"""
    import time
    
    current_time = time.time()
    
    # Use cached result if it's less than 30 seconds old
    if (_mongodb_connection_cache['status'] is not None and 
        current_time - _mongodb_connection_cache['last_check'] < 30):
        return _mongodb_connection_cache['status']
    
    try:
        db = get_db()
        # Try a simple operation to test connection with timeout
        db.command('ping', maxTimeMS=5000)  # 5 second timeout
        _mongodb_connection_cache['status'] = True
        _mongodb_connection_cache['last_check'] = current_time
        return True
    except Exception as e:
        logger.warning(f"MongoDB connection not available: {e}")
        _mongodb_connection_cache['status'] = False
        _mongodb_connection_cache['last_check'] = current_time
        return False

# Fallback data for when MongoDB is not available
_fallback_posts = []
_fallback_profiles = {}

# Cache for MongoDB connection status
_mongodb_connection_cache = {'status': None, 'last_check': 0}

def create_user_profile(user, bio="", interests=None, profile_picture_url=""):
    """Create a user profile in MongoDB"""
    if interests is None:
        interests = []

    profile = UserProfile(
        user_id=str(user.id),
        bio=bio,
        interests=interests,
        profile_picture_url=profile_picture_url
    )
    profile.save()
    return profile

def get_user_profile(user):
    """Get user profile from MongoDB"""
    try:
        return UserProfile.objects.get(user_id=str(user.id))
    except UserProfile.DoesNotExist:
        return None

def update_user_profile(user, bio, interests):
    """Update user profile in MongoDB"""
    try:
        profile = UserProfile.objects.get(user_id=str(user.id))
        profile.bio = bio
        profile.interests = interests
        profile.save()
        return profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        return create_user_profile(user, bio, interests)

def create_post(user, title, content, tags=None):
    """Create a new post in MongoDB"""
    if tags is None:
        tags = []

    post = Post(
        title=title,
        content=content,
        author_id=str(user.id),
        tags=tags,
        likes_count=0,
        liked_by=[]
    )
    post.save()
    return post

def get_all_posts():
    """Get all posts from MongoDB, ordered by creation date"""
    try:
        if not _check_mongodb_connection():
            logger.error("MongoDB connection not available")
            return []
        return Post.objects.order_by('-created_at')
    except Exception as e:
        logger.error(f"Error fetching posts from MongoDB: {e}")
        return []

def get_user_posts(user):
    """Get all posts by a specific user"""
    try:
        if not _check_mongodb_connection():
            return []
        return Post.objects.filter(author_id=str(user.id)).order_by('-created_at')
    except Exception as e:
        logger.error(f"Error fetching user posts from MongoDB: {e}")
        return []

def get_post_by_id(post_id):
    """Get a specific post by ID"""
    try:
        if not _check_mongodb_connection():
            return None
        return Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error fetching post by ID from MongoDB: {e}")
        return None

def update_post(post_id, title, content, tags):
    """Update an existing post"""
    try:
        post = Post.objects.get(id=post_id)
        post.title = title
        post.content = content
        post.tags = tags
        post.save()
        return post
    except Post.DoesNotExist:
        return None

def delete_post(post_id):
    """Delete a post"""
    try:
        post = Post.objects.get(id=post_id)
        post.delete()
        return True
    except Post.DoesNotExist:
        return False

def create_comment(user, post_id, content):
    """Create a comment on a post"""
    comment = Comment(
        post_id=post_id,
        author_id=str(user.id),
        content=content
    )
    comment.save()
    return comment

def get_post_comments(post_id):
    """Get all comments for a specific post"""
    return Comment.objects.filter(post_id=post_id).order_by('created_at')

def like_post(user, post_id):
    """Like a post"""
    try:
        post = Post.objects.get(id=post_id)
        user_id = str(user.id)

        if user_id not in post.liked_by:
            post.liked_by.append(user_id)
            post.likes_count += 1
            post.save()
        return True
    except Post.DoesNotExist:
        return False

def unlike_post(user, post_id):
    """Unlike a post"""
    try:
        post = Post.objects.get(id=post_id)
        user_id = str(user.id)

        if user_id in post.liked_by:
            post.liked_by.remove(user_id)
            post.likes_count -= 1
            post.save()
        return True
    except Post.DoesNotExist:
        return False

def is_post_liked_by_user(user, post_id):
    """Check if a post is liked by a specific user"""
    try:
        post = Post.objects.get(id=post_id)
        return str(user.id) in post.liked_by
    except Post.DoesNotExist:
        return False

def search_posts(query):
    """Search posts by title, content, or tags"""
    return Post.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(tags__icontains=query)
    ).order_by('-created_at')

def get_user_by_id(user_id):
    """Get Django user by ID"""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
