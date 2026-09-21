from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Promote a user to moderator: staff access + the Moderators permission group."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--remove", action="store_true", help="Demote instead of promote."
        )

    def handle(self, username, remove, **options):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No user named '{username}'.")

        group, _ = Group.objects.get_or_create(name="Moderators")

        if remove:
            user.groups.remove(group)
            user.is_staff = False
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{username} is no longer a moderator."))
        else:
            user.groups.add(group)
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{username} can now log into /admin/ and moderate posts."))
