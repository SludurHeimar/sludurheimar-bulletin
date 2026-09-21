from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("post/new/", views.new_post, name="new_post"),
    path("me/posts/", views.my_posts, name="my_posts"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.ThrottledLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="feed"), name="logout"),
    path("privacy/", TemplateView.as_view(template_name="board/privacy.html"), name="privacy"),
    path("terms/", TemplateView.as_view(template_name="board/terms.html"), name="terms"),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="board/password_reset.html",
            email_template_name="board/password_reset_email.txt",
            subject_template_name="board/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="board/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="board/password_reset_confirm.html",
            success_url="/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="board/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
