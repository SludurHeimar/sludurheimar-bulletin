from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SignUpForm, PostForm
from .models import Post, PostStatus, Category, RATE_LIMIT_MINUTES
from .moderation import get_auto_flags
from .throttle import too_many_attempts, throttled_response


def signup(request):
    if request.method == "POST":
        if too_many_attempts(request, "signup", limit=10, window_seconds=600):
            return throttled_response()

        form = SignUpForm(request.POST)
        if form.is_valid():
            if form.is_bot():
                # Pretend it worked; don't create an account or tip off the bot.
                messages.success(request, "Account created. You can post once your first submission is approved.")
                return redirect("feed")
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. You can post once your first submission is approved.")
            return redirect("feed")
    else:
        form = SignUpForm()
    return render(request, "board/signup.html", {"form": form})


class ThrottledLoginView(LoginView):
    template_name = "board/login.html"

    def post(self, request, *args, **kwargs):
        if too_many_attempts(request, "login", limit=15, window_seconds=600):
            return throttled_response()
        return super().post(request, *args, **kwargs)


def feed(request):
    category = request.GET.get("category", "")
    posts = [
        p for p in Post.objects.filter(status=PostStatus.APPROVED).select_related("author")
        if p.is_publicly_visible
    ]
    if category:
        posts = [p for p in posts if p.category == category]
    return render(request, "board/feed.html", {
        "posts": posts,
        "categories": Category.choices,
        "selected_category": category,
    })


@login_required
def new_post(request):
    last_post = Post.objects.filter(author=request.user).order_by("-created_at").first()
    if last_post and timezone.now() - last_post.created_at < timedelta(minutes=RATE_LIMIT_MINUTES):
        wait = RATE_LIMIT_MINUTES - int((timezone.now() - last_post.created_at).total_seconds() // 60)
        messages.error(request, f"You can post again in about {max(wait, 1)} minute(s).")
        return redirect("feed")

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            if form.is_bot():
                messages.success(request, "Submitted. It'll show up once a moderator approves it.")
                return redirect("feed")
            post = form.save(commit=False)
            post.author = request.user
            post.author_email_snapshot = request.user.email
            post.ip_address = request.META.get("REMOTE_ADDR")
            post.status = PostStatus.PENDING
            post.auto_flags = ", ".join(get_auto_flags(post.body))
            post.save()
            messages.success(request, "Submitted. It'll show up once a moderator approves it.")
            return redirect("feed")
    else:
        form = PostForm()
    return render(request, "board/post_form.html", {"form": form})


@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user)
    return render(request, "board/my_posts.html", {"posts": posts})
