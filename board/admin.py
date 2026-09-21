from django.contrib import admin
from django.utils import timezone

admin.site.site_header = "Slúðurheimar"
admin.site.site_title = "Slúðurheimar admin"
admin.site.index_title = "Moderation"

from .models import Post, PostStatus


class ModerationActionsMixin:
    actions = ["approve_posts", "reject_posts"]

    @admin.action(description="Approve selected posts (goes live now)")
    def approve_posts(self, request, queryset):
        updated = queryset.exclude(status=PostStatus.APPROVED).update(
            status=PostStatus.APPROVED, approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} post(s) approved and now live.")

    @admin.action(description="Reject selected posts")
    def reject_posts(self, request, queryset):
        updated = queryset.update(status=PostStatus.REJECTED)
        self.message_user(request, f"{updated} post(s) rejected.")


@admin.register(Post)
class PostAdmin(ModerationActionsMixin, admin.ModelAdmin):
    list_display = ("id", "category", "status", "auto_flags", "author", "created_at", "is_publicly_visible")
    list_filter = ("status", "category")
    search_fields = ("body", "author__username", "author_email_snapshot")
    readonly_fields = ("author_email_snapshot", "ip_address", "created_at", "approved_at", "auto_flags")

    def get_queryset(self, request):
        # Flagged-but-pending posts first, so a moderator sees the ones
        # worth a closer look at the top of the queue.
        qs = super().get_queryset(request)
        return qs.order_by("status", "-auto_flags", "-created_at")


class PostPendingReview(Post):
    """Same table as Post - just a permanently pre-filtered admin view
    so a moderator has one click to the review queue instead of having
    to apply the status filter every time."""

    class Meta:
        proxy = True
        verbose_name = "Post pending review"
        verbose_name_plural = "Posts pending review"


@admin.register(PostPendingReview)
class PostPendingReviewAdmin(ModerationActionsMixin, admin.ModelAdmin):
    list_display = ("id", "category", "auto_flags", "author", "created_at")
    list_filter = ("category",)
    search_fields = ("body", "author__username", "author_email_snapshot")
    readonly_fields = ("author_email_snapshot", "ip_address", "created_at", "auto_flags")

    def get_queryset(self, request):
        qs = super().get_queryset(request).filter(status=PostStatus.PENDING)
        return qs.order_by("-auto_flags", "-created_at")

    def has_add_permission(self, request):
        return False
