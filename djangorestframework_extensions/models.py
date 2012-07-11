from django.dispatch import receiver
from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.management import update_contenttypes
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission


@receiver(post_syncdb)
def ensure_view_permission(app, created_models, **kwargs):
    update_contenttypes(app, created_models, **kwargs)  # This is normally called by post_syncdb, but we cannot guarantee ordering so we call it here

    for m in created_models:
        content_type = ContentType.objects.get_for_model(m)
        meta = m._meta
        obj_name = meta.object_name.lower()

        perm, created = Permission.objects.get_or_create(
            name="Can view %s" % obj_name,
            content_type=content_type,
            codename="view_%s" % obj_name)

        if created:
            print "Added view_%s permission" % obj_name

from djangorestframework_extensions import renderers  # Make sure we register our new renderers
