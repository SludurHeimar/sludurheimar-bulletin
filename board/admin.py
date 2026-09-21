from django.contrib import admin
from django.utils import timezone

from .models import Post, PostStatus


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "status", "author", "created_at", "is_publicly_visible")
    list_filter = ("status", "category")
    search_fields = ("body", "author__username", "author_email_snapshot")
    readonly_fields = ("author_email_snapshot", "ip_address", "created_at", "approved_at")
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
