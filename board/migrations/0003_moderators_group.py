from django.contrib.auth.management import create_permissions
from django.db import migrations


def create_moderators_group(apps, schema_editor):
    # Default model permissions (view_post, change_post, ...) are normally
    # created by a post_migrate signal that fires AFTER all migrations in
    # this run finish - which is too late for a data migration in the same
    # run to use them. Create them explicitly here first.
    app_config = apps.get_app_config("board")
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Post = apps.get_model("board", "Post")

    content_type = ContentType.objects.get_for_model(Post)
    perms = Permission.objects.filter(
        content_type=content_type, codename__in=["view_post", "change_post"]
    )
    group, _ = Group.objects.get_or_create(name="Moderators")
    group.permissions.set(perms)


def remove_moderators_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Moderators").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("board", "0002_post_auto_flags"),
    ]

    operations = [
        migrations.RunPython(create_moderators_group, remove_moderators_group),
    ]
