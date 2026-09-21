from django.contrib import admin
from django.utils import timezone

admin.site.site_header = "Bulletin Board"
admin.site.site_title = "Bulletin Board admin"
admin.site.index_title = "Moderation"

from .models import Post, PostStatus


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "status", "auto_flags", "author", "created_at", "is_publicly_visible")
    list_filter = ("status", "category")
    search_fields = ("body", "author__username", "author_email_snapshot")
    readonly_fields = ("author_email_snapshot", "ip_address", "created_at", "approved_at", "auto_flags")
    actions = ["approve_posts", "reject_posts"]

    def get_queryset(self, request):
        # Flagged-but-pending posts first, so a moderator sees the ones
        # worth a closer look at the top of the queue.
        qs = super().get_queryset(request)
        return qs.order_by("status", "-auto_flags", "-created_at")

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
