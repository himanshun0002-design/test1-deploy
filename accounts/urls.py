from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('create-post/', views.create_post_view, name='create_post'),
    path('post/<str:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<str:post_id>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<str:post_id>/delete/', views.delete_post_view, name='delete_post'),
    path('post/<str:post_id>/like/', views.like_post_view, name='like_post'),
    path('post/<str:post_id>/unlike/', views.unlike_post_view, name='unlike_post'),
    path('health/', views.health_check, name='health_check'),
]
