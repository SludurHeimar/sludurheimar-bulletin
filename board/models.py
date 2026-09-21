from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

# How long an approved post stays visible in the public feed.
LIVE_DAYS = 7
# How much longer after that we keep the post + ip/email around for abuse
# investigation, before it's purged for good. Matches the 1 week live +
# 1 extra week retained decision.
RETENTION_DAYS = LIVE_DAYS + 7

# Character limit for a post body. Placeholder - confirm before launch.
POST_MAX_LENGTH = 1000

# Minimum gap between two posts from the same account, to slow spam.
RATE_LIMIT_MINUTES = 5


class Category(models.TextChoices):
    IDEAS = "ideas", "Ideas"
    STORIES = "stories", "Stories"
    VENTING = "venting", "Venting"
    COMPLAINTS = "complaints", "Complaints"
    OTHER = "other", "Other"


class PostStatus(models.TextChoices):
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    category = models.CharField(max_length=20, choices=Category.choices)
    body = models.CharField(max_length=POST_MAX_LENGTH)

    status = models.CharField(max_length=10, choices=PostStatus.choices, default=PostStatus.PENDING)
    moderator_note = models.CharField(max_length=300, blank=True)

    # Snapshotted at post time, independent of the account, so a later
    # email/account change doesn't rewrite the audit trail. Cleared by the
    # retention job, never shown publicly.
    author_email_snapshot = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.body[:40]}"

    @property
    def is_publicly_visible(self):
        """Approved and still within its 1-week live window."""
        if self.status != PostStatus.APPROVED or not self.approved_at:
            return False
        return timezone.now() < self.approved_at + timedelta(days=LIVE_DAYS)

    @property
    def purge_after(self):
        """When this row (post text + ip + email) should be hard-deleted."""
        anchor = self.approved_at or self.created_at
        return anchor + timedelta(days=RETENTION_DAYS)
