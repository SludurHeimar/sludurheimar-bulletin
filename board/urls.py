from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("post/new/", views.new_post, name="new_post"),
    path("me/posts/", views.my_posts, name="my_posts"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="board/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="feed"), name="logout"),
]
