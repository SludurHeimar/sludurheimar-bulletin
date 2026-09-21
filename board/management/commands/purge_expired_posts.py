from django.core.management.base import BaseCommand
from django.utils import timezone

from board.models import Post


class Command(BaseCommand):
    """Hard-deletes posts (and their stored ip/email) past their retention window.

    Run this on a schedule (e.g. daily via cron). Nothing here soft-deletes:
    once a row is past `purge_after`, it's gone for good, matching the
    1 week live + 1 extra week retained policy.
    """

    help = "Delete posts whose retention window (live + grace period) has passed."

    def handle(self, *args, **options):
        now = timezone.now()
        expired_ids = [p.id for p in Post.objects.all() if p.purge_after <= now]
        count = len(expired_ids)
        Post.objects.filter(id__in=expired_ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Purged {count} expired post(s)."))
