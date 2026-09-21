from django.db import migrations


def create_moderators_group(apps, schema_editor):
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
