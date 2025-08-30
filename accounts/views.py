from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)
from .mongo_utils import (
    create_user_profile, get_user_profile, create_post, get_all_posts, 
    get_user_posts, create_comment, get_post_comments, like_post, 
    unlike_post, update_user_profile, delete_post, update_post,
    search_posts, get_post_by_id
)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create MongoDB profile for the user
            create_user_profile(user)
            # Log the user in after successful registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'Account created successfully for {username}!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:home')

@login_required
def profile(request):
    """User profile view (requires login)"""
    user_profile = get_user_profile(request.user)
    user_posts = get_user_posts(request.user)
    return render(request, 'accounts/profile.html', {
        'user_profile': user_profile,
        'user_posts': user_posts
    })

@login_required
def edit_profile(request):
    """Edit user profile view"""
    user_profile = get_user_profile(request.user)
    
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        interests = request.POST.get('interests', '').split(',') if request.POST.get('interests') else []
        interests = [interest.strip() for interest in interests if interest.strip()]
        
        # Update profile in MongoDB
        update_user_profile(request.user, bio, interests)
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html', {
        'user_profile': user_profile
    })

def home(request):
    """Home page view with login functionality"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Get all posts from MongoDB for display
    try:
        if search_query:
            posts = search_posts(search_query)
        else:
            posts = get_all_posts()
    except Exception as e:
        # If MongoDB is not available, show empty posts list
        posts = []
        messages.warning(request, 'Posts are temporarily unavailable. Please try again later.')
        logger.error(f"Error fetching posts: {e}")
    
    return render(request, 'home.html', {
        'posts': posts,
        'search_query': search_query
    })

@login_required
def create_post_view(request):
    """Create a new post"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        tags = request.POST.get('tags', '').split(',') if request.POST.get('tags') else []
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        if title and content:
            post = create_post(request.user, title, content, tags)
            messages.success(request, 'Post created successfully!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Please provide both title and content.')
    
    return render(request, 'accounts/create_post.html')

@login_required
def edit_post_view(request, post_id):
    """Edit an existing post"""
    post = get_post_by_id(post_id)
    
    if not post:
        messages.error(request, 'Post not found.')
        return redirect('accounts:home')
    
    # Check if user owns the post
    if str(post.author_id) != str(request.user.id):
        messages.error(request, 'You can only edit your own posts.')
        return redirect('accounts:home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        tags = request.POST.get('tags', '').split(',') if request.POST.get('tags') else []
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        if title and content:
            update_post(post_id, title, content, tags)
            messages.success(request, 'Post updated successfully!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Please provide both title and content.')
    
    return render(request, 'accounts/edit_post.html', {
        'post': post
    })

@login_required
def delete_post_view(request, post_id):
    """Delete a post"""
    post = get_post_by_id(post_id)
    
    if not post:
        messages.error(request, 'Post not found.')
        return redirect('accounts:home')
    
    # Check if user owns the post
    if str(post.author_id) != str(request.user.id):
        messages.error(request, 'You can only delete your own posts.')
        return redirect('accounts:home')
    
    if request.method == 'POST':
        delete_post(post_id)
        messages.success(request, 'Post deleted successfully!')
        return redirect('accounts:home')
    
    return render(request, 'accounts/delete_post.html', {
        'post': post
    })

@login_required
def post_detail_view(request, post_id):
    """View a single post with comments"""
    post = get_post_by_id(post_id)
    
    if not post:
        messages.error(request, 'Post not found.')
        return redirect('accounts:home')
    
    comments = get_post_comments(post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            create_comment(request.user, post_id, content)
            messages.success(request, 'Comment added successfully!')
            return redirect('accounts:post_detail', post_id=post_id)
    
    return render(request, 'accounts/post_detail.html', {
        'post': post,
        'comments': comments
    })

@login_required
@require_POST
def like_post_view(request, post_id):
    """Like a post (AJAX)"""
    try:
        like_post(request.user, post_id)
        return JsonResponse({'status': 'success', 'action': 'liked'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def unlike_post_view(request, post_id):
    """Unlike a post (AJAX)"""
    try:
        unlike_post(request.user, post_id)
        return JsonResponse({'status': 'success', 'action': 'unliked'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def health_check(request):
    """Health check endpoint for debugging"""
    from .mongo_utils import _check_mongodb_connection
    from django.utils import timezone
    
    mongodb_status = _check_mongodb_connection()
    
    return JsonResponse({
        'status': 'healthy',
        'mongodb_connected': mongodb_status,
        'timestamp': timezone.now().isoformat()
    })
